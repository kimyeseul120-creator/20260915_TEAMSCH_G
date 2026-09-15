from datetime import datetime

from app.extensions import db

LEAVE_TYPES = {
    "annual": "연차",
    "half_day": "반차",
    "sick": "병가",
    "official": "공가",
    "etc": "기타",
}


class Leave(db.Model):
    __tablename__ = "leaves"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False, default="annual")
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "leave_type": self.leave_type,
            "leave_type_label": LEAVE_TYPES.get(self.leave_type, self.leave_type),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "reason": self.reason,
        }
