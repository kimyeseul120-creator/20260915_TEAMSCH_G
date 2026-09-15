from datetime import datetime

from app.extensions import db

SCHEDULE_TYPES = {
    "meeting": "미팅",
    "work": "업무",
    "outside": "외근",
    "business_trip": "출장",
    "training": "교육",
    "vacation": "휴가",
    "half_day": "반차",
    "personal": "개인 일정",
    "etc": "기타",
}


class Schedule(db.Model):
    __tablename__ = "schedules"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    schedule_type = db.Column(db.String(20), nullable=False, default="etc")
    start_datetime = db.Column(db.DateTime, nullable=False)
    end_datetime = db.Column(db.DateTime, nullable=False)
    is_all_day = db.Column(db.Boolean, nullable=False, default=False)
    location = db.Column(db.String(200))
    meeting_url = db.Column(db.String(300))
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])
    participants = db.relationship(
        "ScheduleParticipant", back_populates="schedule", cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "schedule_type": self.schedule_type,
            "schedule_type_label": SCHEDULE_TYPES.get(self.schedule_type, self.schedule_type),
            "start_datetime": self.start_datetime.isoformat(),
            "end_datetime": self.end_datetime.isoformat(),
            "is_all_day": self.is_all_day,
            "location": self.location,
            "meeting_url": self.meeting_url,
            "created_by": self.created_by,
            "creator_name": self.creator.name if self.creator else None,
            "participants": [p.user.name for p in self.participants if p.user],
        }
