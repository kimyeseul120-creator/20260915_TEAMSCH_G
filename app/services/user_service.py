import re

from app.extensions import db
from app.models import User, Department
from app.services.auth_service import count_active_admins


class UserServiceError(Exception):
    pass


def _normalize_code(code):
    return (code or "").strip().upper()


# 부서명 -> 사용자코드 접두사. 목록에 없는(또는 새로 만든) 부서는 "USER"로 대체된다.
DEPARTMENT_CODE_PREFIXES = {
    "개발팀": "DEV",
    "기획팀": "PLAN",
    "영업팀": "SALES",
    "인사팀": "HR",
    "경영지원팀": "MGT",
}


def generate_user_code(role, department_id=None):
    """
    권한/부서를 바탕으로 다음 사용자코드를 자동 생성한다.
    예: 개발팀 조직원 -> DEV001, DEV002 ... / 관리자 -> ADMIN001, ADMIN002 ...
    """
    if role == "admin":
        prefix = "ADMIN"
    else:
        dept = Department.query.get(department_id) if department_id else None
        prefix = DEPARTMENT_CODE_PREFIXES.get(dept.name, "USER") if dept else "USER"

    pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
    max_num = 0
    for (code,) in db.session.query(User.user_code).filter(User.user_code.like(f"{prefix}%")):
        m = pattern.match(code)
        if m:
            max_num = max(max_num, int(m.group(1)))
    return f"{prefix}{max_num + 1:03d}"


def create_user(name, department_id=None, position=None, email=None,
                 phone=None, role="member", is_active=True, user_code=None):
    """
    user_code를 지정하지 않으면 부서/권한 기준으로 자동 생성한다
    (직접 지정도 가능하지만, 화면에서는 자동 생성만 사용한다).
    """
    name = (name or "").strip()
    if not name:
        raise UserServiceError("이름은 필수입니다.")
    if role not in ("member", "admin"):
        raise UserServiceError("권한 값이 올바르지 않습니다.")

    if user_code:
        user_code = _normalize_code(user_code)
        if User.query.filter_by(user_code=user_code).first():
            raise UserServiceError("이미 사용 중인 사용자코드입니다.")
    else:
        # 동시 생성 시 코드가 겹칠 수 있어 충돌하면 다음 번호로 한 번 더 시도한다.
        for _ in range(5):
            user_code = generate_user_code(role, department_id)
            if not User.query.filter_by(user_code=user_code).first():
                break
        else:
            raise UserServiceError("사용자코드를 자동 생성하지 못했습니다. 다시 시도해주세요.")

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
