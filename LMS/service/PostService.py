import os
import uuid
from common.session import Session

class PostService:
    #파일 게시물 저장
    @staticmethod
    def save_post(member_id, title, content, files=None, upload_folder='uploads/'):
        """게시글과 첨부파일을 동시에 저장 (트랜잭션 처리)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 게시글 먼저 저장
                sql_post = "INSERT INTO posts (member_id, title, content) VALUES (%s, %s, %s)"
                cursor.execute(sql_post, (member_id, title, content))
                # 2. 방금 INSERT된 게시글의 ID(PK) 가져오기
                post_id = cursor.lastrowid

                # 3. 다중 파일 처리
                if files:
                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower()
                            save_name = f"{uuid.uuid4().hex}.{ext}"
                            file_path = os.path.join(upload_folder, save_name)

                            file.save(file_path)
                            sql_file = """INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                          VALUES (%s, %s, %s, %s)"""
                            cursor.execute(sql_file, (post_id, origin_name, save_name, file_path))
                conn.commit()
                return True
        except Exception as e:
            print(f"Error saving post: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def get_posts():
        """작성자 이름과 첨부파일 개수를 함께 조회"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                        SELECT p.*, m.name as writer_name,
                                (SELECT COUNT(*) FROM attachments WHERE post_id = p.id) as file_count
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        ORDER BY p.created_at DESC
                        """
                cursor.execute(sql)
                return cursor.fetchall()
        finally:
            conn.close()

    @staticmethod
    def get_post_detail(post_id):
        """게시글 상세 정보와 첨부파일 함께 조회"""
        conn = Session.get_connection()
        try :
            with conn.cursor() as cursor:
                cursor.execute("UPDATE posts SET view_count = view_count + 1 WHERE id = %s", (post_id,))
                sql_post = """
                        SELECT p.*, m.name as writer_name
                        FROM posts p
                        JOIN members m ON p.member_id = m.id
                        WHERE p.id = %s
                        """
                cursor.execute(sql_post, (post_id,))
                post = cursor.fetchone()

                cursor.execute("SELECT * FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall()
                conn.commit()
                return post, files
        finally:
            conn.close()

    @staticmethod
    def delete_post(post_id, member_id, user_role=None, upload_folder='uploads/'):
        """게시글 및 관련 실제 파일 삭제 (권한 확인 포함)"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                # 권한 확인
                cursor.execute("SELECT member_id FROM posts WHERE id = %s", (post_id,))
                post = cursor.fetchone()
                if not post:
                    return False
                
                if post['member_id'] != member_id and user_role != 'admin':
                    return False

                cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                files = cursor.fetchall()

                for f in files:
                    file_path = os.path.join(upload_folder, f['save_name'])
                    if os.path.exists(file_path):
                        os.remove(file_path)

                sql = "DELETE FROM posts WHERE id = %s"
                cursor.execute(sql, (post_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"Delete Error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    @staticmethod
    def update_post(post_id, title, content, files=None, upload_folder='uploads/'):
        """게시글 수정 및 다중 파일 교체"""
        conn = Session.get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute("UPDATE posts SET title=%s, content=%s WHERE id=%s", (title, content, post_id))

                if files and any(f.filename != '' for f in files):
                    cursor.execute("SELECT save_name FROM attachments WHERE post_id = %s", (post_id,))
                    old_files = cursor.fetchall()
                    for old in old_files:
                        old_path = os.path.join(upload_folder, old['save_name'])
                        if os.path.exists(old_path):
                            os.remove(old_path)

                    cursor.execute("DELETE FROM attachments WHERE post_id = %s", (post_id,))

                    for file in files:
                        if file and file.filename != '':
                            origin_name = file.filename
                            ext = origin_name.rsplit('.', 1)[1].lower()
                            save_name = f"{uuid.uuid4().hex}.{ext}"
                            file_path = os.path.join(upload_folder, save_name)
                            file.save(file_path)
                            cursor.execute("""
                                    INSERT INTO attachments (post_id, origin_name, save_name, file_path)
                                    VALUES (%s, %s, %s, %s)
                                """, (post_id, origin_name, save_name, file_path))

                conn.commit()
                return True
        except Exception as e:
            print(f"Update Error: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
