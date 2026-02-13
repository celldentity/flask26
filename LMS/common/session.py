import pymysql

class Session:

    @staticmethod
    def get_connection(): # 데이터베이스에 연결용 코드
        return pymysql.connect(
            host='192.168.0.155',
            user='ksb',
            password='1234',  # 본인의 비밀번호로 변경
            db='mbc',
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )