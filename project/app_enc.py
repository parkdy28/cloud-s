from flask import Blueprint, render_template, request, jsonify
import mysql.connector
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.hashes import SHA256
import os
import logging
from initialize_db import execute_query

# Flask Blueprint 설정
enc_bp = Blueprint('enc', __name__, template_folder='templates')

# 로그 설정
logging.basicConfig(level=logging.DEBUG)

# 테스트 페이지 라우트 추가 (GET 요청 시 test.html 렌더링)
@enc_bp.route("/test", methods=["GET"])
def test_page():
    return render_template("test.html")  # templates 폴더 내 test.html 렌더링

# AES 암호화 함수
def aes_encrypt(data, password):
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        iterations=100000
    )
    aes_key = kdf.derive(password.encode())
    iv = os.urandom(16)
    cipher = Cipher(algorithms.AES(aes_key), modes.CFB(iv))
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data.encode()) + encryptor.finalize()
    return encrypted_data, salt, iv

# 암호화 페이지 (GET 요청 시 렌더링)
@enc_bp.route('/encrypt/encryption', methods=['GET'])
def encryption():
    return render_template("encryption.html")

# 암호화 처리 라우트 (POST 요청 시)
@enc_bp.route("/encrypt/encryption", methods=["POST"])
def encrypt_route():
    password = request.form.get("password")
    username = request.form.get("username")  # user_id 대신 username 받음

    # 사용자 이름 확인
    if not username:
        logging.error("사용자 이름이 없습니다.")
        return jsonify({"error": "사용자 이름이 필요합니다."}), 400

    # 비밀번호 검증
    if len(password) != 6 or not password.isdigit():
        logging.error("잘못된 비밀번호 형식.")
        return jsonify({"error": "6자리 숫자로 된 비밀번호를 입력하세요."}), 400

    # users 테이블에서 user_id 조회
    user_data = execute_query(
        "SELECT id FROM users WHERE username = %s",
        (username,),
        fetch_one=True
    )

    if not user_data:
        logging.error(f"해당 사용자 이름({username})이 존재하지 않습니다.")
        return jsonify({"error": "해당 사용자 이름이 존재하지 않습니다."}), 404

    user_id = user_data['id']  # 조회한 user_id 사용

    # scores 테이블에서 사용자 점수 데이터 조회
    score_data = execute_query(
        "SELECT pwd_score, last_login_score, failed_login_attempt_score, remote_access_score, total_score "
        "FROM scores WHERE user_id = %s",
        (user_id,),
        fetch_one=True
    )

    if not score_data:
        logging.error(f"해당 사용자 ID({user_id})에 대한 점수 데이터가 없습니다.")
        return jsonify({"error": "해당 사용자 ID에 대한 점수 데이터가 없습니다."}), 404

    # 점수 데이터를 문자열로 변환
    scores = f"{score_data['pwd_score']},{score_data['last_login_score']},{score_data['failed_login_attempt_score']},{score_data['remote_access_score']},{score_data['total_score']}"

    # 암호화 수행
    encrypted_data, salt, iv = aes_encrypt(scores, password)

    try:
        # 데이터베이스에 암호화된 데이터 저장
        execute_query("""
            INSERT INTO encrypted_data (user_id, encrypted_data, salt, iv, encrypted_private_key)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, encrypted_data, salt, iv, b""), commit=True)

        logging.info(f"암호화 데이터가 사용자 {username}({user_id})에 대해 성공적으로 데이터베이스에 기록되었습니다.")
        return jsonify({"message": "성공적으로 암호화되었습니다!"})

    except Exception as e:
        logging.error(f"데이터베이스 기록 실패: {e}")
        return jsonify({"error": "데이터베이스에 기록하는 데 실패했습니다."}), 500

