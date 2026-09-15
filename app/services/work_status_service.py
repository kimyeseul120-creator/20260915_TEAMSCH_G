from datetime import datetime

from app.extensions import db
from app.models import WorkStatus, STATUS_CHOICES


def get_status(user_id):
    return WorkStatus.query.filter_by(user_id=user_id).first()


def set_status(user_id, status, memo=None):
    if status not in STATUS_CHOICES:
        raise ValueError("올바르지 않은 상태 값입니다.")
    row = get_status(user_id)
    if not row:
        row = WorkStatus(user_id=user_id, status=status, memo=memo, start_datetime=datetime.utcnow())
        db.session.add(row)
    else:
        row.status = status
        row.memo = memo
        row.start_datetime = datetime.utcnow()
    db.session.commit()
    return row
