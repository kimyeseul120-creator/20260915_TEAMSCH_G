"""
개인 메모 보안 테스트 (요구사항서 33절 필수 테스트 항목).

핵심: 본인 메모는 CRUD 가능, 타인의 메모는 관리자를 포함해 그 누구도
조회/수정/삭제할 수 없어야 하며, 서버가 이를 404로 응답해 존재 여부까지 숨긴다.
"""
from app.extensions import db
from app.models import User, Memo


def _login(client, code):
    return client.post("/login", data={"user_code": code}, follow_redirects=True)


def _create_user(app, code, name, role="member"):
    with app.app_context():
        u = User(user_code=code, name=name, role=role, is_active=True)
        db.session.add(u)
        db.session.commit()
        return u.id


def _create_memo(app, user_id, title):
    with app.app_context():
        memo = Memo(user_id=user_id, title=title, content="비밀 내용")
        db.session.add(memo)
        db.session.commit()
        return memo.id


def test_user_can_crud_own_memo(app, client):
    _create_user(app, "USER010", "홍길동")
    _login(client, "USER010")

    res = client.post("/api/memos", json={"title": "내 메모", "content": "내용"})
    assert res.status_code == 201
    memo_id = res.get_json()["memo"]["id"]

    res = client.get(f"/api/memos/{memo_id}")
    assert res.status_code == 200
    assert res.get_json()["memo"]["title"] == "내 메모"

    res = client.put(f"/api/memos/{memo_id}", json={"title": "수정된 메모"})
    assert res.status_code == 200
    assert res.get_json()["memo"]["title"] == "수정된 메모"

    res = client.delete(f"/api/memos/{memo_id}")
    assert res.status_code == 200

    res = client.get(f"/api/memos/{memo_id}")
    assert res.status_code == 404


def test_other_member_cannot_read_memo(app, client):
    owner_id = _create_user(app, "USER011", "홍길동")
    _create_user(app, "USER012", "김철수")
    memo_id = _create_memo(app, owner_id, "홍길동의 비밀")

    _login(client, "USER012")
    res = client.get(f"/api/memos/{memo_id}")
    assert res.status_code == 404  # 403이 아니라 404로 존재 자체를 숨김


def test_admin_cannot_read_other_users_memo(app, client):
    owner_id = _create_user(app, "USER013", "홍길동")
    _create_user(app, "ADMIN010", "관리자", role="admin")
    memo_id = _create_memo(app, owner_id, "홍길동의 비밀")

    _login(client, "ADMIN010")
    res = client.get(f"/api/memos/{memo_id}")
    assert res.status_code == 404


def test_other_member_cannot_update_or_delete_memo(app, client):
    owner_id = _create_user(app, "USER014", "홍길동")
    _create_user(app, "USER015", "김철수")
    memo_id = _create_memo(app, owner_id, "원본 제목")

    _login(client, "USER015")

    res = client.put(f"/api/memos/{memo_id}", json={"title": "해킹 시도"})
    assert res.status_code == 404

    res = client.delete(f"/api/memos/{memo_id}")
    assert res.status_code == 404

    with app.app_context():
        memo = Memo.query.get(memo_id)
        assert memo is not None
        assert memo.title == "원본 제목"


def test_memo_list_only_returns_own_memos(app, client):
    owner_id = _create_user(app, "USER016", "홍길동")
    other_id = _create_user(app, "USER017", "김철수")
    _create_memo(app, owner_id, "홍길동 메모")
    _create_memo(app, other_id, "김철수 메모")

    _login(client, "USER016")
    res = client.get("/api/memos")
    titles = [m["title"] for m in res.get_json()["memos"]]
    assert titles == ["홍길동 메모"]
