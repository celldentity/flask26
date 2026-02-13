from common.session import Session
from domain.Board import Board

class BoardService:

    @staticmethod
    def get_list():
        """게시판 목록 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT b.*, m.name as writer_name 
                    FROM boards b 
                    JOIN members m ON b.member_id = m.id 
                    ORDER BY b.id DESC
                """
                cursor.execute(sql)
                rows = cursor.fetchall()
                return [Board.from_db(row) for row in rows]
        finally:
            conn.close()

    @staticmethod
    def get_view(board_id):
        """게시글 상세 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT b.*, m.name as writer_name, m.uid as writer_uid
                    FROM boards b
                    JOIN members m ON b.member_id = m.id
                    WHERE b.id = %s
                """
                cursor.execute(sql, (board_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                return Board.from_db(row)
        finally:
            conn.close()

    @staticmethod
    def write(member_id, title, content):
        """게시글 저장"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "INSERT INTO boards (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql, (member_id, title, content))
                conn.commit()
                return True
        except Exception as e:
            print(f"Write error: {e}")
            return False
        finally:
            conn.close()

    @staticmethod
    def edit(board_id, title, content, member_id):
        """게시글 수정 (작성자 확인 포함)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 본인 확인
                cursor.execute("SELECT member_id FROM boards WHERE id = %s", (board_id,))
                row = cursor.fetchone()
                if not row or row['member_id'] != member_id:
                    return False, "수정 권한이 없습니다."

                sql = "UPDATE boards SET title=%s, content=%s WHERE id=%s"
                cursor.execute(sql, (title, content, board_id))
                conn.commit()
                return True, "수정 성공"
        except Exception as e:
            print(f"Edit error: {e}")
            return False, "저장 중 에러가 발생했습니다."
        finally:
            conn.close()

    @staticmethod
    def delete(board_id, member_id, user_role=None):
        """게시글 삭제 (작성자 또는 관리자 확인 포함)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 권한 확인을 위해 게시글 조회
                cursor.execute("SELECT member_id FROM boards WHERE id = %s", (board_id,))
                row = cursor.fetchone()
                if not row:
                    return False
                
                # 작성자 본인이거나 관리자인 경우 삭제 가능
                if row['member_id'] == member_id or user_role == 'admin':
                    sql = "DELETE FROM boards WHERE id = %s"
                    cursor.execute(sql, (board_id,))
                    conn.commit()
                    return cursor.rowcount > 0
                return False
        except Exception as e:
            print(f"Delete error: {e}")
            return False
        finally:
            conn.close()
