from app.extensions import db
from app.models import User


def _create_member(app, code="USER001", name="테스트유저", active=True):
    with app.app_context():
        u = User(user_code=code, name=name, role="member", is_active=active)
        db.session.add(u)
        db.session.commit()
        return u.id


def test_login_success(app, client):
    _create_member(app)
    res = client.post("/login", data={"user_code": "USER001"}, follow_redirects=True)
    assert res.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_login_unknown_code_rejected(app, client):
    res = client.post("/login", data={"user_code": "NOPE"}, follow_redirects=True)
    assert "등록되지 않은 사용자코드입니다.".encode() in res.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_login_inactive_user_blocked(app, client):
    _create_member(app, code="INACTIVE1", active=False)
    res = client.post("/login", data={"user_code": "INACTIVE1"}, follow_redirects=True)
    assert "비활성화된 사용자입니다.".encode() in res.data
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_logout_clears_session(app, client):
    _create_member(app, code="USER002")
    client.post("/login", data={"user_code": "USER002"})
    client.post("/logout")
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None


def test_unauthenticated_dashboard_redirects_to_login(client):
    res = client.get("/", follow_redirects=False)
    assert res.status_code == 302
    assert "/login" in res.headers["Location"]
