import os
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory

# 리팩토링된 서비스들 임포트
from service.MemberService import MemberService
from service.BoardService import BoardService
from service.ScoreService import ScoreService
from service.PostService import PostService

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# 파일 업로드 설정
UPLOAD_FOLDER = 'uploads/'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# ---------------------------------------------------------
# 1. 회원 관련 (Auth & Member)
# ---------------------------------------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    uid = request.form.get('uid')
    upw = request.form.get('upw')
    
    user = MemberService.login(uid, upw)
    if user:
        session['user_id'] = user['id']
        session['user_name'] = user['name']
        session['user_uid'] = user['uid']
        session['user_role'] = user['role']
        return redirect(url_for('index'))
    else:
        return "<script>alert('아이디나 비번이 틀렸습니다.');history.back();</script>"

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

    success, message = MemberService.signup(uid, password, name)
    if success:
        return f"<script>alert('{message}'); location.href='/login';</script>"
    else:
        return f"<script>alert('{message}'); history.back();</script>"

@app.route('/member/edit', methods=['GET', 'POST'])
def member_edit():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        user_info = MemberService.get_member_info(session['user_id'])
        return render_template('member_edit.html', user=user_info)

    new_name = request.form.get('name')
    new_pw = request.form.get('password')

    if MemberService.update_member(session['user_id'], new_name, new_pw):
        session['user_name'] = new_name
        return "<script>alert('정보가 수정되었습니다.'); location.href='/mypage';</script>"
    return "<script>alert('수정 중 오류 발생'); history.back();</script>"

@app.route('/mypage')
def mypage():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_info = MemberService.get_member_info(session['user_id'])
    board_count = MemberService.get_board_count(session['user_id'])
    return render_template('mypage.html', user=user_info, board_count=board_count)

# ---------------------------------------------------------
# 2. 일반 게시판 (Board)
# ---------------------------------------------------------

@app.route('/board')
def board_list():
    boards = BoardService.get_list()
    return render_template('board_list.html', boards=boards)

@app.route('/board/write', methods=['GET', 'POST'])
def board_write():
    if 'user_id' not in session:
        return '<script>alert("로그인 후 이용 가능합니다."); location.href="/login";</script>'
    
    if request.method == 'GET':
        return render_template('board_write.html')

    title = request.form.get('title')
    content = request.form.get('content')
    if BoardService.write(session['user_id'], title, content):
        return redirect(url_for('board_list'))
    return "저장 중 에러 발생"

@app.route('/board/view/<int:board_id>')
def board_view(board_id):
    board = BoardService.get_view(board_id)
    if not board:
        return "<script>alert('존재하지 않는 게시글입니다.'); history.back();</script>"
    return render_template('board_view.html', board=board)

@app.route('/board/edit/<int:board_id>', methods=['GET', 'POST'])
def board_edit(board_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        board = BoardService.get_view(board_id)
        if not board:
            return "<script>alert('존재하지 않는 게시글입니다.'); history.back();</script>"
        if board.member_id != session.get('user_id'):
            return "<script>alert('수정 권한이 없습니다.'); history.back();</script>"
        return render_template('board_edit.html', board=board)

    title = request.form.get('title')
    content = request.form.get('content')
    success, message = BoardService.edit(board_id, title, content, session['user_id'])
    if success:
        return redirect(url_for('board_view', board_id=board_id))
    return f"<script>alert('{message}'); history.back();</script>"

@app.route('/board/delete/<int:board_id>')
def board_delete(board_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 삭제 권한 체크 및 삭제를 서비스에서 수행
    if BoardService.delete(board_id, session['user_id'], session.get('user_role')):
        return redirect(url_for('board_list'))
    return "<script>alert('삭제 권한이 없거나 오류 발생'); history.back();</script>"

# ---------------------------------------------------------
# 3. 성적 관리 (Score)
# ---------------------------------------------------------

@app.route('/score/members')
def score_members():
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.'); history.back();</script>"
    members = ScoreService.get_member_list_for_score()
    return render_template('score_member_list.html', members=members)

@app.route('/score/add')
def score_add():
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.'); history.back();</script>"
    
    target_uid = request.args.get('uid')
    target_name = request.args.get('name')
    score_obj, name = ScoreService.get_score_status(target_uid)
    
    return render_template('score_form.html', 
                           target_uid=target_uid, 
                           target_name=name or target_name, 
                           score=score_obj)

@app.route('/score/save', methods=['POST'])
def score_save():
    if session.get('user_role') not in ('admin', 'manager'):
        return "권한 오류", 403

    target_uid = request.form.get('target_uid')
    kor = int(request.form.get('korean', 0))
    eng = int(request.form.get('english', 0))
    math = int(request.form.get('math', 0))

    success, message = ScoreService.save_score(target_uid, kor, eng, math)
    return f"<script>alert('{message}'); location.href='/score/list';</script>"

@app.route('/score/list')
def score_list():
    if session.get('user_role') not in ('admin', 'manager'):
        return "<script>alert('권한이 없습니다.'); history.back();</script>"
    scores = ScoreService.get_all_scores()
    return render_template('score_list.html', scores=scores)

@app.route('/score/my')
def score_my():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    score = ScoreService.get_my_score(session['user_id'])
    return render_template('score_my.html', score=score)

# ---------------------------------------------------------
# 4. 파일 게시판 (FilesBoard - PostService)
# ---------------------------------------------------------

@app.route('/filesboard')
def filesboard_list():
    posts = PostService.get_posts()
    return render_template('filesboard_list.html', posts=posts)

@app.route('/filesboard/write', methods=['GET', 'POST'])
def filesboard_write():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        files = request.files.getlist('files')
        if PostService.save_post(session['user_id'], title, content, files):
            return "<script>alert('게시글 등록 성공'); location.href='/filesboard';</script>"
        return "<script>alert('등록 실패'); history.back();</script>"

    return render_template('filesboard_write.html')

@app.route('/filesboard/view/<int:post_id>')
def filesboard_view(post_id):
    post, files = PostService.get_post_detail(post_id)
    if not post:
        return "<script>alert('존재하지 않는 게시글입니다.'); location.href='/filesboard';</script>"
    return render_template('filesboard_view.html', post=post, files=files)

@app.route('/filesboard/delete/<int:post_id>')
def filesboard_delete(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # 권한 확인 및 삭제를 서비스 레이어에서 처리
    if PostService.delete_post(post_id, session['user_id'], session.get('user_role')):
        return "<script>alert('삭제 성공'); location.href='/filesboard';</script>"
    return "<script>alert('삭제 권한이 없거나 이미 삭제된 게시글입니다.'); history.back();</script>"

@app.route('/filesboard/edit/<int:post_id>', methods=['GET', 'POST'])
def filesboard_edit(post_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'GET':
        post, files = PostService.get_post_detail(post_id)
        if post['member_id'] != session['user_id']:
            return "<script>alert('권한이 없습니다.'); history.back();</script>"
        return render_template('filesboard_edit.html', post=post, files=files)

    title = request.form.get('title')
    content = request.form.get('content')
    files = request.files.getlist('files')
    if PostService.update_post(post_id, title, content, files):
        return f"<script>alert('수정 성공'); location.href='/filesboard/view/{post_id}';</script>"
    return "<script>alert('수정 실패'); history.back();</script>"

@app.route('/download/<path:filename>')
def download_file(filename):
    origin_name = request.args.get('origin_name')
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True, download_name=origin_name)

# ---------------------------------------------------------
# 5. 메인
# ---------------------------------------------------------

@app.route('/')
def index():
    return render_template('main.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5645, debug=True)