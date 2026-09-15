import traceback

try:
    from app import create_app

    app = create_app()
except Exception:
    # Vercel 등 서버리스 환경에서 콜드스타트 시점에 앱 생성이 실패하면 원인을 알 수 없어
    # 임시로 에러 내용을 그대로 응답하는 최소 Flask 앱으로 대체한다.
    # (원인 파악 후 이 try/except는 제거할 것)
    _tb = traceback.format_exc()
    from flask import Flask

    app = Flask(__name__)

    @app.route("/", defaults={"path": ""})
    @app.route("/<path:path>")
    def _debug(path):
        return f"<pre>{_tb}</pre>", 500


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5050)
