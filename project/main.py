from flask import Flask
from app_dash import dash_bp
from app_score import score_bp
from app_enc import enc_bp

app = Flask(__name__)
app.secret_key = "your_secret_key"  # 세션 암호화 키

# 블루프린트 등록
app.register_blueprint(dash_bp, url_prefix="/")
app.register_blueprint(score_bp, url_prefix="/score")
app.register_blueprint(enc_bp, url_prefix="/enc")

if __name__ == "__main__":
    app.run(debug=True)

