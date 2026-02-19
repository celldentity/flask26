# pip install flask
import random
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from common.session import Session
from service import *
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 회원 정보 조회
            sql = "SELECT id, name, uid, role  FROM members WHERE uid = %s AND password = %s"
            cursor.execute(sql, (uid, upw))
            user = cursor.fetchone()

            if user:
                session['user_id'] = user['id']
                session['user_name'] = user['name']
                session['user_uid'] = user['uid']
                session['user_role'] = user['role']

                return redirect(url_for('index'))
            else:
                return "<script>alert('아이디 또는 비밀번호가 틀렸습니다.'); history.back();</script>"
    finally:
        conn.close()

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/join', methods=['GET', 'POST'])
def join():
    if request.method == 'GET':
        return render_template('join.html')

    uid = request.form.get('uid')
    password = request.form.get('password')
    name = request.form.get('name')

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM members WHERE uid = %s", (uid,))
            if cursor.fetchone():
                return "<script>alert('이미 존재하는 아이디입니다.'); history.back();</script>"

            sql = "INSERT INTO members (uid, password, name) VALUES (%s, %s, %s)"
            cursor.execute(sql, (uid, password, name))
            conn.commit()

            return "<script>alert('회원가입이 완료되었습니다!'); location.href='/login';</script>"
    except Exception as e:
        print(f"회원가입 에러: {e}")
        return "가입 중 오류가 발생했습니다."
    finally:
        conn.close()

@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            if request.method == 'GET':
                # 기존 정보 불러오기
                cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
                user_info = cursor.fetchone()
                return render_template('member_edit.html', user=user_info)

            # POST 요청: 정보 업데이트
            new_name = request.form.get('name')
            new_pw = request.form.get('password')

            if new_pw:  # 비밀번호 입력 시에만 변경
                sql = "UPDATE members SET password = %s WHERE id = %s"
                cursor.execute(sql, (new_pw, session['user_id']))
            else:  # 이름만 변경
                sql = "UPDATE members SET name = %s WHERE id = %s"
                cursor.execute(sql, (new_name, session['user_id']))

            conn.commit()
            session['user_name'] = new_name  # 세션 이름 정보도 갱신
            return "<script>alert('정보가 수정되었습니다.'); location.href='/mypage';</script>"
    finally:
        conn.close()

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = Session.get_connection()
    try:
        with conn.cursor() as cursor:
            # 1. 내 상세 정보 조회
            cursor.execute("SELECT * FROM members WHERE id = %s", (session['user_id'],))
            user_info = cursor.fetchone()

            return render_template('mypage.html', user=user_info)
    finally:
        conn.close()
# ---------------------------------------------------------
# 2. 타이핑 서비스 (Typing)
# ---------------------------------------------------------
# 1. 코딩 명언 데이터 내장 (id, 제목, 내용)
QUOTES = [
    {"id": 1, "ko_title": "리누스 토발즈", "en_title": "Linus Torvalds", "content": "말은 쉽다. 코드를 보여줘."},
    {"id": 2, "ko_title": "마틴 파울러", "en_title": "Martin Fowler", "content": "바보라도 컴퓨터가 이해할 수 있는 코드는 짤 수 있다. 좋은 프로그래머는 사람이 이해할 수 있는 코드를 짠다."},
    {"id": 3, "ko_title": "켄트 베크", "en_title": "Kent Beck", "content": "먼저 작동하게 하라. 그 다음 올바르게 만들어라. 그 다음 빠르게 만들어라."},
    {"id": 4, "ko_title": "로버트 C. 마틴", "en_title": "Robert C. Martin", "content": "코드는 깨끗해야 한다. 그렇지 않으면 프로젝트는 금방 엉망이 된다."},
    {"id": 5, "ko_title": "빌 게이츠", "en_title": "Bill Gates", "content": "소프트웨어 개발에서 가장 중요한 것은 문제를 해결하는 능력이다."},
    {"id": 6, "ko_title": "스티브 잡스", "en_title": "Steve Jobs", "content": "이 나라 모든 사람은 코딩을 배워야 한다. 코딩은 생각하는 법을 가르쳐주기 때문이다."},
    {"id": 7, "ko_title": "에츠허르 데이크스트라", "en_title": "Edsger W. Dijkstra", "content": "프로그래밍은 단순함의 예술이다."},
    {"id": 8, "ko_title": "그레이스 호퍼", "en_title": "Grace Hopper", "content": "한 번 해보는 것이 백 번 듣는 것보다 낫다."},
    {"id": 9, "ko_title": "존 존슨", "en_title": "John Johnson", "content": "먼저 문제를 해결하라. 그런 다음 코드를 써라."},
    {"id": 10, "ko_title": "Bjarne Stroustrup", "en_title": "비야네 스트롭스트룹", "content": "내 코드가 작동하는지 확인하는 것보다 중요한 것은 내가 왜 그렇게 짰는지 아는 것이다."}
]

@app.route('/typing')
def typing_page():
    # 언어 설정 (기본값 'ko')
    lang = request.args.get('lang')
    if lang in ['ko', 'en']:
        session['typing_lang'] = lang
    current_lang = session.get('typing_lang', 'ko')

    # 2. 내장된 리스트에서 무작위로 하나 선택
    typing_data = random.choice(QUOTES)

    # 3. HTML 템플릿에 맞게 데이터 구조 매핑
    display_data = {
        "id": typing_data["id"],
        "title": typing_data["ko_title"] if current_lang == 'ko' else typing_data["en_title"],
        "content": typing_data["content"],
        "lang": current_lang
    }

    return render_template('typing_practice.html', typing=display_data)

@app.route('/typing/complete', methods=['POST'])
def typing_complete():
    # DB 연동이 없으므로 성공 메시지만 반환 (또는 포인트 로직 추가 가능)
    return jsonify({"success": True})

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host='0.0.0.0', port=5700, debug=True)