from datetime import datetime

from app.extensions import db


class OnlineMeeting(db.Model):
    """온라인 회의(채팅) 방. 참여자는 별도 테이블 없이, 메시지를 보낸 사용자로 자동 구성된다."""

    __tablename__ = "online_meetings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    is_closed = db.Column(db.Boolean, nullable=False, default=False)
    summary = db.Column(db.Text)
    summarized_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User")
    messages = db.relationship(
        "MeetingMessage",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="MeetingMessage.id",
    )

    def participant_names(self):
        names = []
        for m in self.messages:
            name = m.user.name if m.user else "알수없음"
            if name not in names:
                names.append(name)
        return names

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "is_closed": self.is_closed,
            "creator_name": self.creator.name if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "message_count": len(self.messages),
            "has_summary": bool(self.summary),
        }


class MeetingMessage(db.Model):
    __tablename__ = "meeting_messages"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("online_meetings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    meeting = db.relationship("OnlineMeeting", back_populates="messages")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "알수없음",
            "content": self.content,
            "time": self.created_at.strftime("%H:%M") if self.created_at else "",
        }
