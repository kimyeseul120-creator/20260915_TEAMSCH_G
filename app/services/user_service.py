from app.extensions import db
from app.models import User
from app.services.auth_service import count_active_admins


class UserServiceError(Exception):
    pass


def _normalize_code(code):
    return (code or "").strip().upper()


def create_user(user_code, name, department_id=None, position=None, email=None,
                 phone=None, role="member", is_active=True):
    user_code = _normalize_code(user_code)
    name = (name or "").strip()
    if not user_code or not name:
        raise UserServiceError("사용자코드와 이름은 필수입니다.")
    if role not in ("member", "admin"):
        raise UserServiceError("권한 값이 올바르지 않습니다.")
    if User.query.filter_by(user_code=user_code).first():
        raise UserServiceError("이미 사용 중인 사용자코드입니다.")

    user = User(
        user_code=user_code,
        name=name,
        department_id=department_id or None,
        position=position,
        email=email,
        phone=phone,
        role=role,
        is_active=is_active,
    )
    db.session.add(user)
    db.session.commit()
    return user


def update_user(user, name=None, position=None, email=None, phone=None, department_id=None):
    if name:
        user.name = name.strip()
    if position is not None:
        user.position = position
    if email is not None:
        user.email = email
    if phone is not None:
        user.phone = phone
    if department_id is not None:
        user.department_id = department_id or None
    db.session.commit()
    return user


def change_user_code(user, new_code):
    new_code = _normalize_code(new_code)
    if not new_code:
        raise UserServiceError("사용자코드는 비어 있을 수 없습니다.")
    if new_code != user.user_code and User.query.filter_by(user_code=new_code).first():
        raise UserServiceError("이미 사용 중인 사용자코드입니다.")
    user.user_code = new_code
    db.session.commit()
    return user


def set_department(user, department_id):
    user.department_id = department_id or None
    db.session.commit()
    return user


def set_role(user, role):
    if role not in ("member", "admin"):
        raise UserServiceError("권한 값이 올바르지 않습니다.")
    if user.role == "admin" and role == "member" and count_active_admins(exclude_user_id=user.id) == 0:
        raise UserServiceError("최소 1명의 활성 관리자 계정이 존재해야 합니다.")
    user.role = role
    db.session.commit()
    return user


def set_active(user, is_active):
    if user.role == "admin" and user.is_active and not is_active:
        if count_active_admins(exclude_user_id=user.id) == 0:
            raise UserServiceError("최소 1명의 활성 관리자 계정이 존재해야 합니다.")
    user.is_active = is_active
    db.session.commit()
    return user


def delete_user(user):
    if user.role == "admin" and count_active_admins(exclude_user_id=user.id) == 0:
        raise UserServiceError("최소 1명의 활성 관리자 계정이 존재해야 합니다.")
    db.session.delete(user)
    db.session.commit()
