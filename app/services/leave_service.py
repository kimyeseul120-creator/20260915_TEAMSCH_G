from datetime import date

from app.extensions import db
from app.models import Leave, LEAVE_TYPES


def list_my_leaves(user_id):
    return Leave.query.filter_by(user_id=user_id).order_by(Leave.start_date.desc()).all()


def list_leaves_on(target_date=None):
    target_date = target_date or date.today()
    return Leave.query.filter(Leave.start_date <= target_date, Leave.end_date >= target_date).all()


def create_leave(user_id, leave_type, start_date, end_date, reason=None):
    if leave_type not in LEAVE_TYPES:
        raise ValueError("올바르지 않은 휴무 유형입니다.")
    if end_date < start_date:
        raise ValueError("종료일은 시작일보다 빠를 수 없습니다.")
    leave = Leave(
        user_id=user_id, leave_type=leave_type,
        start_date=start_date, end_date=end_date, reason=reason,
    )
    db.session.add(leave)
    db.session.commit()
    return leave


def get_my_leave_or_none(leave_id, user_id):
    return Leave.query.filter_by(id=leave_id, user_id=user_id).first()


def delete_leave(leave_id, user_id):
    leave = get_my_leave_or_none(leave_id, user_id)
    if not leave:
        return False
    db.session.delete(leave)
    db.session.commit()
    return True
