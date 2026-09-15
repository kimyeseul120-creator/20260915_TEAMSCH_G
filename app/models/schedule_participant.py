from datetime import datetime

from app.extensions import db


class ScheduleParticipant(db.Model):
    __tablename__ = "schedule_participants"

    id = db.Column(db.Integer, primary_key=True)
    schedule_id = db.Column(db.Integer, db.ForeignKey("schedules.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    participation_status = db.Column(db.String(20), nullable=False, default="invited")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    schedule = db.relationship("Schedule", back_populates="participants")
    user = db.relationship("User")

    __table_args__ = (
        db.UniqueConstraint("schedule_id", "user_id", name="uq_schedule_participant"),
    )
