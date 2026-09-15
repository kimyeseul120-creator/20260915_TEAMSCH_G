import traceback
from datetime import timedelta

from flask import Flask

from app.config import Config
from app.extensions import db, csrf


def create_app(config_class=Config):
    try:
        return _build_app(config_class)
    except Exception:
        # 서버리스 콜드스타트 등에서 앱 생성 자체가 실패하면 원인을 알 수 없으므로,
        # 임시로 에러 내용을 그대로 보여주는 최소 앱을 반환한다.
        # (run.py의 `app = create_app()`이 항상 top-level Flask 앱을 갖도록 이 구조를 유지)
        tb = traceback.format_exc()
        fallback = Flask(__name__)

        @fallback.route("/", defaults={"path": ""})
        @fallback.route("/<path:path>")
        def _debug(path):
            return f"<pre>{tb}</pre>", 500

        return fallback


def _build_app(config_class):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.permanent_session_lifetime = timedelta(
        minutes=app.config["PERMANENT_SESSION_LIFETIME_MINUTES"]
    )

    db.init_app(app)
    csrf.init_app(app)

    from app.routes import auth, dashboard, user, admin, department, schedule, work_status, leave, task, memo

    app.register_blueprint(auth.bp)
    app.register_blueprint(dashboard.bp)
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(department.bp)
    app.register_blueprint(schedule.bp)
    app.register_blueprint(work_status.bp)
    app.register_blueprint(leave.bp)
    app.register_blueprint(task.bp)
    app.register_blueprint(memo.bp)

    with app.app_context():
        db.create_all()
        _seed_initial_data(app)

    return app


def _seed_initial_data(app):
    """
    최초 실행 시(사용자 테이블이 비어있을 때)에만 부트스트랩 관리자 1명과
    예시 부서 몇 개를 만들어, 로그인할 방법이 전혀 없는 상황을 방지한다.
    """
    from app.models import User, Department

    if Department.query.count() == 0:
        for name in ["개발팀", "기획팀", "영업팀", "인사팀", "경영지원팀"]:
            db.session.add(Department(name=name))
        db.session.commit()

    if User.query.count() == 0:
        admin_code = app.config["INITIAL_ADMIN_CODE"]
        admin_name = app.config["INITIAL_ADMIN_NAME"]
        db.session.add(
            User(user_code=admin_code, name=admin_name, role="admin", is_active=True)
        )
        db.session.commit()
        app.logger.warning(
            "초기 관리자 계정을 생성했습니다. 사용자코드: %s (필요 시 로그인 후 사용자코드를 변경하세요)",
            admin_code,
        )
