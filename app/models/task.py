from datetime import datetime

from app.extensions import db

TASK_STATUSES = {
    "planned": "예정",
    "in_progress": "진행중",
    "on_hold": "보류",
    "done": "완료",
}


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="planned")
    progress = db.Column(db.Integer, nullable=False, default=0)
    priority = db.Column(db.String(10), default="normal")
    start_date = db.Column(db.Date)
    due_date = db.Column(db.Date)
    project_name = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "status_label": TASK_STATUSES.get(self.status, self.status),
            "progress": self.progress,
            "priority": self.priority,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "project_name": self.project_name,
        }
