from flask import Blueprint, render_template, redirect, url_for, request, session
import mysql.connector
from datetime import datetime

dash_bp = Blueprint('dash', __name__, template_folder='templates')

DATABASE_CONFIG = {
    'host': '192.168.74.128',
    'port': '3306',
    'user': 'root',
    'password': 'alic0828*',  # 실제 MySQL 비밀번호
    'database': 'account_management'
}

def db_connect():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None

@dash_bp.route('/')
def home():
    return redirect(url_for('dash.login'))  # 루트 경로에서 로그인 페이지로 리디렉션


# 로그인 페이지 처리
@dash_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        # 데이터베이스에서 사용자 인증
        conn = db_connect()
        if conn is None:
            return "데이터베이스 연결 실패"

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM accounts WHERE name = %s", (name,))
        user = cursor.fetchone()

        if user:
            account_id = user["account_id"]  # account_id 가져오기
            
            # 로그인 시도 횟수가 10번 이상이면 로그인 차단
            if user['failed_login_attempt'] >= 10:
                return render_template('login.html', error="계정이 잠겼습니다. 관리자에게 문의하세요.")
            
            # 비밀번호 확인
            if user['password'] == password:
                # 로그인 성공: last_login 업데이트
                cursor.execute("UPDATE accounts SET last_login = %s WHERE account_id = %s", (datetime.now(), account_id))
                session['account_id'] = user['account_id']
                session['account_type'] = user['account_type']
                conn.commit()
                return redirect(url_for('dash.dashboard'))  # 대시보드로 리디렉션
            else:
                # 비밀번호가 틀리면 failed_login_attempt 증가
                cursor.execute("UPDATE accounts SET failed_login_attempt = failed_login_attempt + 1 WHERE account_id = %s", (account_id,))
                conn.commit()
                return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")
        else:
            return render_template('login.html', error="아이디 또는 비밀번호가 틀렸습니다.")
        
        cursor.close()
        conn.close()
    
    return render_template('login.html')  # GET 요청 시 로그인 페이지 표시


# 대시보드 페이지
@dash_bp.route('/dashboard', methods=['GET'])
def dashboard():
    if 'account_id' not in session:
        return redirect(url_for('dash.login'))  # 로그인 안 되어 있으면 로그인 페이지로 리디렉션

    # 주계정일 경우 점수 측정 버튼도 제공
    is_main_account = session.get('account_type') == 'main'

    return render_template('dashboard.html', is_main_account=is_main_account)  # 대시보드 화면

# 로그아웃 처리
@dash_bp.route('/logout')
def logout():
    session.clear()  # 세션 초기화 (로그아웃 처리)
    return redirect(url_for('dash.login'))  # 로그인 페이지로 리디렉션

