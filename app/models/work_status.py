from datetime import datetime

from app.extensions import db

STATUS_CHOICES = {
    "working": "🟢 근무중",
    "remote": "🔵 재택근무",
    "outside": "🟡 외근",
    "business_trip": "🟣 출장",
    "vacation": "🔴 휴가",
    "etc": "🟠 기타",
}


class WorkStatus(db.Model):
    __tablename__ = "work_status"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default="working")
    start_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    end_datetime = db.Column(db.DateTime)
    memo = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="work_status")

    def to_dict(self):
        return {
            "status": self.status,
            "status_label": STATUS_CHOICES.get(self.status, self.status),
            "memo": self.memo,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
