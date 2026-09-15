from datetime import datetime

from app.extensions import db


class OnlineMeeting(db.Model):
    """온라인 회의(채팅) 방. 참여자 = 개설자 + 초대된 사람(MeetingParticipant) + 실제로 채팅을 보낸 사람."""

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
    invited = db.relationship(
        "MeetingParticipant",
        back_populates="meeting",
        cascade="all, delete-orphan",
        order_by="MeetingParticipant.invited_at",
    )

    def invited_user_ids(self):
        return {p.user_id for p in self.invited}

    def participant_names(self):
        """초대된 사람 + 실제로 채팅한 사람을 순서대로(중복 없이) 합친 이름 목록."""
        names = []
        if self.creator and self.creator.name not in names:
            names.append(self.creator.name)
        for p in self.invited:
            if p.user and p.user.name not in names:
                names.append(p.user.name)
        for m in self.messages:
            name = m.user.name if m.user else "알수없음"
            if name not in names:
                names.append(name)
        return names

    def is_member(self, user):
        """이 회의의 개설자 / 초대받은 사람 / 관리자 여부."""
        if not user:
            return False
        if user.is_admin or user.id == self.created_by:
            return True
        return user.id in self.invited_user_ids()

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


class MeetingParticipant(db.Model):
    """회의에 초대된 사람. 실제로 채팅을 하지 않아도 초대된 시점부터 참여자로 표시된다."""

    __tablename__ = "meeting_participants"

    id = db.Column(db.Integer, primary_key=True)
    meeting_id = db.Column(db.Integer, db.ForeignKey("online_meetings.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    invited_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)

    meeting = db.relationship("OnlineMeeting", back_populates="invited")
    user = db.relationship("User", foreign_keys=[user_id])

    __table_args__ = (
        db.UniqueConstraint("meeting_id", "user_id", name="uq_meeting_participant"),
    )
