from datetime import datetime

from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    user_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(50), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("departments.id"), nullable=True)
    position = db.Column(db.String(30))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(30))
    role = db.Column(db.String(10), nullable=False, default="member")  # member / admin
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    department = db.relationship("Department", back_populates="users")
    work_status = db.relationship("WorkStatus", back_populates="user", uselist=False)

    @property
    def is_admin(self):
        return self.role == "admin"

    def to_dict(self, include_private=False):
        data = {
            "id": self.id,
            "user_code": self.user_code,
            "name": self.name,
            "department_id": self.department_id,
            "department": self.department.name if self.department else None,
            "position": self.position,
            "role": self.role,
            "is_active": self.is_active,
        }
        if include_private:
            data["email"] = self.email
            data["phone"] = self.phone
        return data
