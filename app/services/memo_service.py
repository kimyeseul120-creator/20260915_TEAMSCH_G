"""
개인 메모 서비스.

핵심 원칙(요구사항 22~23, 29, 32): 개인 메모는 작성자 본인만 조회/수정/삭제할 수 있고,
관리자를 포함해 그 누구도 예외가 될 수 없다. 아래 모든 조회 함수는 user_id로
직접 필터링하며, "다른 사람의 메모"는 존재 자체를 노출하지 않기 위해 404로
취급한다 (403이 아님 - 존재 여부까지 숨긴다).
"""
from app.extensions import db
from app.models import Memo


def list_my_memos(user_id, keyword=None):
    query = Memo.query.filter_by(user_id=user_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Memo.title.ilike(like), Memo.content.ilike(like)))
    return query.order_by(Memo.updated_at.desc()).all()


def get_my_memo_or_none(memo_id, user_id):
    """소유자가 아니면 무조건 None을 반환한다 (관리자 포함 예외 없음)."""
    return Memo.query.filter_by(id=memo_id, user_id=user_id).first()


def create_memo(user_id, title, content=""):
    title = (title or "").strip()
    if not title:
        raise ValueError("메모 제목을 입력해주세요.")
    memo = Memo(user_id=user_id, title=title, content=content or "")
    db.session.add(memo)
    db.session.commit()
    return memo


def update_memo(memo_id, user_id, title=None, content=None):
    memo = get_my_memo_or_none(memo_id, user_id)
    if not memo:
        return None
    if title is not None:
        memo.title = title.strip() or memo.title
    if content is not None:
        memo.content = content
    db.session.commit()
    return memo


def delete_memo(memo_id, user_id):
    memo = get_my_memo_or_none(memo_id, user_id)
    if not memo:
        return False
    db.session.delete(memo)
    db.session.commit()
    return True
