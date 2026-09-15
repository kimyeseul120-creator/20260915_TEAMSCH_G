from datetime import datetime

from app.extensions import db


class Memo(db.Model):
    """
    개인 메모: 반드시 작성자 본인만 조회/수정/삭제할 수 있다 (관리자도 예외 없음).
    소유권 검증은 이 모델을 다루는 모든 라우트/서비스에서 user_id로 직접 필터링해
    수행하며, 프론트엔드에서만 숨기는 방식으로 처리하지 않는다.
    """

    __tablename__ = "memos"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
