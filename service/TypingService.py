import gspread
import os
from common.session import Session
from oauth2client.service_account import ServiceAccountCredentials
from domain.Typing import Typing


# 기존에 사용하시는 DB 연결 모듈을 임포트하세요 (예: from common.db import get_connection)

class TypingService:

    @classmethod
    def get_random_sentence(cls, lang='ko'):
        conn = None
        try:
            conn = Session.get_connection()
            with conn.cursor() as cursor:
                sql = "SELECT * FROM typing_contents ORDER BY RAND() LIMIT 1"
                cursor.execute(sql)
                row = cursor.fetchone()
                # 딕셔너리를 Typing 객체로 변환해서 리턴
                return Typing.from_dict(row, lang)
        finally:
            if conn: conn.close()


    @classmethod
    def sync_with_google_sheets(cls):
        conn = None
        """구글 시트 데이터를 DB와 동기화"""
        try:
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            key_path = os.path.join(base_path, 'static', 'Keys', 'typing_key.json')  # 파일명이 typing_key.json 인지 확인!

            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds = ServiceAccountCredentials.from_json_keyfile_name(key_path, scope)
            client = gspread.authorize(creds)

            # 시트 열기 (파일명: 타이핑)
            sheet = client.open("타이핑").get_worksheet(0)
            rows = sheet.get_all_values()[1:]

            print(f"DEBUG: 시트에서 가져온 행 수: {len(rows)}")  # 데이터 로드 확인용

            conn = Session.get_connection()
            cursor = conn.cursor()

            sync_count = 0
            for row in rows:
                if len(row) < 5: continue  # 데이터가 부족한 행 건너뛰기

                # 중복 체크
                cursor.execute("SELECT id FROM typing_contents WHERE ko_content = %s", (row[2],))

                if not cursor.fetchone():
                    sql = """INSERT INTO typing_contents (ko_title, ko_content, en_title, en_content)
                             VALUES (%s, %s, %s, %s)"""
                    cursor.execute(sql, (row[1], row[2], row[3], row[4]))
                    sync_count += 1

            conn.commit()
            print(f"DEBUG: DB에 저장된 신규 데이터 수: {sync_count}")  # 저장 확인용
            return {"success": True, "count": sync_count}
        except Exception as e:
            print("\n" + "=" * 50)
            print(f"!!! 실제 에러 원인: {str(e)}")
            print("=" * 50 + "\n")
            return {"success": False, "error": str(e)}
        finally:
            if conn:  # [수정] conn이 존재할 때만 close 하도록 변경
                conn.close()


    @classmethod
    def increase_hit_count(cls, content_id):
        """타이핑 완료 시 해당 지문의 hit_count를 1 증가"""
        try:
            conn = Session.get_connection()
            cursor = conn.cursor()
            sql = "UPDATE typing_contents SET hit_count = hit_count + 1 WHERE id = %s"
            cursor.execute(sql, (content_id,))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()