import mysql.connector
from mysql.connector import Error

# MySQL 연결 설정
DATABASE_CONFIG = {
    'host': 'localhost',
    'port': '3306',
    'user': 'root',
    'password': 'alic0828*',  # 여기에 실제 MySQL 비밀번호 입력
    'database': 'account_management'
}

def get_db_connection():
    """데이터베이스 연결을 반환하는 함수"""
    try:
        conn = mysql.connector.connect(**DATABASE_CONFIG)
        if conn.is_connected():
            print("MySQL 연결 성공")
            return conn
    except Error as e:
        print(f"MySQL 연결 실패: {e}")
        return None

def execute_query(query, params=None, commit=False, fetch_one=False, fetch_all=False):
    """SQL 실행 함수: SELECT, INSERT, UPDATE, DELETE 모두 지원"""
    conn = get_db_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params or ())

        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()

        if commit:
            conn.commit()

        return result
    except Error as e:
        print(f"SQL 실행 오류: {e}")
        conn.rollback()
        return None
    finally:
        cursor.close()
        conn.close()

