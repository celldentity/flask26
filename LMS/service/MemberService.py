from common.session import Session
from domain.Member import Member

class MemberService:

    @staticmethod
    def login(uid, upw):
        """웹 로그인용: 사용자 정보 반환 (딕셔너리 형태)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT id, name, uid, role FROM members WHERE uid = %s AND password = %s"
                cursor.execute(sql, (uid, upw))
                return cursor.fetchone() # 세션 저장을 위해 딕셔너리 반환 유지
        finally:
            conn.close()

    @staticmethod
    def signup(uid, password, name):
        """웹 회원가입용: 성공 여부와 메시지 반환"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 중복 체크
                cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
                if cursor.fetchone():
                    return False, "이미 존재하는 아이디입니다."

                sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
                cursor.execute(sql, (uid, password, name))
                conn.commit()
                return True, "회원가입이 완료되었습니다."
        except Exception as e:
            print(f"Signup error: {e}")
            return False, "가입 중 오류가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def get_member_info(member_id):
        """회원 정보 조회 (Member 객체 반환)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM members WHERE id = %s", (member_id,))
                row = cursor.fetchone()
                return Member.from_db(row)
        finally:
            conn.close()

    @staticmethod
    def update_member(member_id, name, password=None):
        """회원 정보 수정"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                if password:
                    sql = "UPDATE members SET name = %s, password = %s WHERE id = %s"
                    cursor.execute(sql, (name, password, member_id))
                else:
                    sql = "UPDATE members SET name = %s WHERE id = %s"
                    cursor.execute(sql, (name, member_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"Update error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def get_board_count(member_id):
        """사용자가 작성한 게시글 개수 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) as board_count FROM boards WHERE member_id = %s", (member_id,))
                return cursor.fetchone()['board_count']
        finally:
            conn.close()