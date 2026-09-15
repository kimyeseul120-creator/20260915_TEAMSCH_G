"""
사용자/권한 관리 테스트 - 사용자코드 고유성, 마지막 관리자 보호(요구사항 12, 26, 33).
"""
import pytest

from app.models import User
from app.services import user_service
from app.services.user_service import UserServiceError


def test_duplicate_user_code_rejected(app):
    with app.app_context():
        user_service.create_user("DUP001", "사용자1")
        with pytest.raises(UserServiceError):
            user_service.create_user("DUP001", "사용자2")


def test_user_code_uniqueness_case_insensitive(app):
    with app.app_context():
        user_service.create_user("dup002", "사용자1")
        with pytest.raises(UserServiceError):
            user_service.create_user("DUP002", "사용자2")  # 대문자로 정규화되어 충돌해야 함


def test_last_admin_cannot_be_demoted(app):
    with app.app_context():
        admin = User.query.filter_by(user_code="ADMIN001").first()
        with pytest.raises(UserServiceError):
            user_service.set_role(admin, "member")


def test_last_admin_cannot_be_deactivated(app):
    with app.app_context():
        admin = User.query.filter_by(user_code="ADMIN001").first()
        with pytest.raises(UserServiceError):
            user_service.set_active(admin, False)


def test_last_admin_cannot_be_deleted(app):
    with app.app_context():
        admin = User.query.filter_by(user_code="ADMIN001").first()
        with pytest.raises(UserServiceError):
            user_service.delete_user(admin)


def test_admin_role_change_allowed_when_another_admin_exists(app):
    with app.app_context():
        user_service.create_user("ADMIN002", "관리자2", role="admin")
        admin1 = User.query.filter_by(user_code="ADMIN001").first()
        user_service.set_role(admin1, "member")  # 다른 관리자가 있으므로 허용되어야 함
        assert admin1.role == "member"


def test_department_assignment_reflected_immediately(app):
    with app.app_context():
        from app.services import department_service

        dept = department_service.create_department("QA팀")
        user = user_service.create_user("QA001", "테스터")
        user_service.set_department(user, dept.id)
        assert user.department_id == dept.id
        assert user.department.name == "QA팀"
