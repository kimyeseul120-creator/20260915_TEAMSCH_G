from app.extensions import db
from app.models import Department


class DepartmentServiceError(Exception):
    pass


def create_department(name, description=None):
    name = (name or "").strip()
    if not name:
        raise DepartmentServiceError("부서명은 필수입니다.")
    if Department.query.filter_by(name=name).first():
        raise DepartmentServiceError("이미 존재하는 부서명입니다.")
    dept = Department(name=name, description=description)
    db.session.add(dept)
    db.session.commit()
    return dept


def update_department(dept, name=None, description=None):
    if name:
        name = name.strip()
        existing = Department.query.filter_by(name=name).first()
        if existing and existing.id != dept.id:
            raise DepartmentServiceError("이미 존재하는 부서명입니다.")
        dept.name = name
    if description is not None:
        dept.description = description
    db.session.commit()
    return dept


def set_active(dept, is_active):
    dept.is_active = is_active
    db.session.commit()
    return dept


def delete_department(dept):
    if dept.users:
        raise DepartmentServiceError(
            "소속된 사용자가 있는 부서는 삭제할 수 없습니다. 먼저 사용자를 다른 부서로 옮기거나 비활성화하세요."
        )
    db.session.delete(dept)
    db.session.commit()
