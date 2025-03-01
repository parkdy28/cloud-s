from flask import Blueprint, render_template, request, session, redirect, url_for, Flask, jsonify
import mysql.connector
from datetime import datetime

score_bp = Blueprint('score', __name__, template_folder='templates')

DATABASE_CONFIG = {
    'host': '192.168.74.128',
    'port': '3306',
    'user': 'root',
    'password': 'alic0828*',  # 실제 MySQL 비밀번호
    'database': 'account_management'
}

# Flask 애플리케이션 객체 생성
app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 세션을 위한 secret_key 설정

def db_connect():
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        print("데이터베이스 연결 성공!")
        return conn
    except mysql.connector.Error as e:
        print(f"데이터베이스 연결 오류: {e}")
        return None

# 점수 측정 및 저장
@score_bp.route('/score', methods=['POST'])
def score():
    if 'account_id' not in session:
        return redirect(url_for('dash.login'))  # 로그인 안 되어 있으면 로그인 페이지로 리디렉션

    account_id = session['account_id']
    conn = db_connect()
    if conn is None:
        return "데이터베이스 연결 실패"

    cursor = conn.cursor(dictionary=True)

    # user_id 가져오기
    cursor.execute("SELECT user_id FROM accounts WHERE account_id = %s", (account_id,))
    user_result = cursor.fetchone()
    if not user_result:
        return "해당 account_id에 대한 user_id를 찾을 수 없습니다."

    user_id = user_result['user_id']

    # 1. pwd_score 가져오기
    cursor.execute("SELECT pwd_score FROM accounts WHERE account_id = %s", (account_id,))
    pwd_score = cursor.fetchone()['pwd_score']

    # 2. last_login 확인 후 점수 계산 (1주일 이내 접속 기준 0~25점)
    cursor.execute("SELECT last_login FROM accounts WHERE account_id = %s", (account_id,))
    last_login = cursor.fetchone()['last_login']
    if last_login:
        days_diff = (datetime.now() - last_login).days
        last_login_score = max(0, 25 - days_diff)
    else:
        last_login_score = 0

    # 3. failed_login_attempt 체크
    cursor.execute("SELECT failed_login_attempt FROM accounts WHERE account_id = %s", (account_id,))
    result = cursor.fetchone()
    failed_attempts = result['failed_login_attempt'] if result else 0


    # failed_login_attempts에 따라 점수 부여 (0~25점)
    if failed_attempts == 0:
        failed_attempts_score = 25
    elif failed_attempts == 1:
        failed_attempts_score = 20
    elif failed_attempts == 2:
        failed_attempts_score = 15
    elif failed_attempts == 3:
        failed_attempts_score = 10
    else:
        failed_attempts_score = 0

    # 4. remote_access 체크 (주계정만 원격접속이 가능)
    cursor.execute("SELECT u.remote_access FROM users u JOIN accounts a ON u.id = a.user_id WHERE a.account_id = %s", (account_id,))
    remote_access = cursor.fetchone()['remote_access']
    remote_access_score = 25 if remote_access == 1 else 0

    # 동일 user_id를 가진 main, sub 계정 점수 합산
    cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (user_id,))
    accounts = cursor.fetchall()

    total_pwd_score = sum([account['pwd_score'] for account in accounts])
    total_last_login_score = sum([max(0, 25 - (datetime.now() - account['last_login']).days if account['last_login'] else 0) for account in accounts])
    total_failed_attempts_score = sum([failed_attempts_score for account in accounts])  # 같은 방식으로 계산
    total_remote_access_score = sum([remote_access_score for account in accounts])

    # 총점 계산 (최대 200점)
    total_score = total_pwd_score + total_last_login_score + total_failed_attempts_score + total_remote_access_score
    total_score = min(total_score, 200)  # 총점이 200점을 넘지 않도록 제한

    # 리스크 레벨 계산 (50점 미만이면 위험)
    risk_level = "위험" if total_score < 50 else "안전"


    # 7. scores 테이블 업데이트
    try:
        update_score_query = """
            UPDATE scores
            SET
                pwd_score = %s,
                last_login_score = %s,
                failed_login_attempt_score = %s,
                remote_access_score = %s,
                total_score = %s,
                created_at = NOW()
            WHERE user_id = %s
        """
        cursor.execute(update_score_query, (total_pwd_score, total_last_login_score, total_failed_attempts_score, total_remote_access_score, total_score, user_id))

        if cursor.rowcount == 0:
            print("업데이트된 행이 없습니다. 삽입으로 진행합니다.")
            insert_score_query = """
                INSERT INTO scores (user_id, pwd_score, last_login_score, failed_login_attempt_score, remote_access_score, total_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, NOW())
            """
            cursor.execute(insert_score_query, (user_id, total_pwd_score, total_last_login_score, total_failed_attempts_score, total_remote_access_score, total_score))
        else:
            print(f"업데이트된 행 수: {cursor.rowcount}")

        # 커밋
        conn.commit()
    except mysql.connector.Error as e:
        print(f"SQL 오류: {e}")
        conn.rollback()  # 오류 발생 시 롤백

    cursor.close()
    conn.close()

    # 결과 반환
    return render_template('score.html', total_score=total_score, risk_level=risk_level)

# score.py

@score_bp.route('/encrypt/encryption', methods=['GET'])
def encryption_redirect():
    return redirect(url_for('enc.encryption'))  # encryption.html로 이동

