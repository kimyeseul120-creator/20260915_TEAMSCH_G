from datetime import timedelta

from flask import Flask, request, flash, redirect, url_for
from flask_wtf.csrf import CSRFError

from app.config import Config
from app.extensions import db, csrf


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.permanent_session_lifetime = timedelta(
        minutes=app.config["PERMANENT_SESSION_LIFETIME_MINUTES"]
    )

    db.init_app(app)
    csrf.init_app(app)

    from app.routes import auth, dashboard, user, admin, department, schedule, work_status, leave, task, memo, meeting

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
    app.register_blueprint(meeting.bp)

    @app.errorhandler(400)
    def _handle_bad_request(e):
        """
        여러 계정/탭이 같은 브라우저를 동시에 쓰거나, 페이지를 오래 열어둔 채로
        요청을 보내면 보안 토큰(CSRF)이 이미 최신 값으로 바뀌어 있어 요청이
        거부될 수 있다. 이는 CSRFProtect가 정상적으로 위조 요청을 막은 것이지만,
        실제 사용자 입장에서는 그냥 "Bad Request" 흰 화면만 보이므로, 로그인
        화면으로 안내해 다시 시도할 수 있게 한다 (계정 자체의 문제가 아님).
        CSRF와 무관한 진짜 잘못된 요청은 원래 400 화면을 그대로 보여준다.
        """
        description = getattr(e, "description", "") or ""
        if isinstance(e, CSRFError) or "CSRF" in description or "referrer" in description.lower():
            flash("보안 정보가 만료되었습니다. 다시 시도해주세요.")
            return redirect(url_for("auth.login"))
        return e

    @app.after_request
    def _disable_caching_for_dynamic_pages(response):
        """
        Vercel은 기본적으로 응답에 "Cache-Control: public, max-age=0, must-revalidate"를
        붙이는데, 이 페이지들은 로그인 세션·CSRF 토큰처럼 사용자마다 달라야 하는 값을
        담고 있어 캐시되면 안 된다. 정적 파일(/static/...)은 그대로 두고, 나머지 응답에는
        캐시하지 말라는 헤더를 명시적으로 덮어써서 "CSRF tokens do not match" 같은
        오류(캐시된 옛 페이지를 여러 사용자가 같이 받는 문제)를 방지한다.
        """
        if not request.path.startswith("/static/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            response.headers["Pragma"] = "no-cache"
        return response

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
