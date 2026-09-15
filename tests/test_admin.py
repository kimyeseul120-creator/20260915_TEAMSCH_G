"""
사용자/권한 관리 테스트 - 사용자코드 고유성/자동생성, 마지막 관리자 보호(요구사항 12, 26, 33).
"""
import pytest

from app.models import User
from app.services import user_service
from app.services.user_service import UserServiceError


def test_duplicate_user_code_rejected(app):
    with app.app_context():
        user_service.create_user(name="사용자1", user_code="DUP001")
        with pytest.raises(UserServiceError):
            user_service.create_user(name="사용자2", user_code="DUP001")


def test_user_code_uniqueness_case_insensitive(app):
    with app.app_context():
        user_service.create_user(name="사용자1", user_code="dup002")
        with pytest.raises(UserServiceError):
            user_service.create_user(name="사용자2", user_code="DUP002")  # 대문자로 정규화되어 충돌해야 함


def test_user_code_auto_generated_by_role(app):
    with app.app_context():
        member = user_service.create_user(name="일반직원")
        admin = user_service.create_user(name="관리자후보", role="admin")
        assert member.user_code == "USER001"
        assert admin.user_code == "ADMIN002"  # 부트스트랩 ADMIN001 다음 번호


def test_user_code_auto_generated_sequential_per_prefix(app):
    with app.app_context():
        from app.services import department_service

        dept = department_service.create_department("개발팀 테스트용")
        # 매핑에 없는 부서명이므로 USER 접두사를 사용해야 한다
        u1 = user_service.create_user(name="사용자1", department_id=dept.id)
        u2 = user_service.create_user(name="사용자2", department_id=dept.id)
        assert u1.user_code == "USER001"
        assert u2.user_code == "USER002"


def test_user_code_auto_generated_known_department_prefix(app):
    with app.app_context():
        from app.models import Department

        # "개발팀"은 앱 최초 기동 시 시드되는 기본 부서 중 하나이다.
        dept = Department.query.filter_by(name="개발팀").first()
        user = user_service.create_user(name="개발자", department_id=dept.id)
        assert user.user_code == "DEV001"


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
        user_service.create_user(name="관리자2", role="admin", user_code="ADMIN002")
        admin1 = User.query.filter_by(user_code="ADMIN001").first()
        user_service.set_role(admin1, "member")  # 다른 관리자가 있으므로 허용되어야 함
        assert admin1.role == "member"


def test_department_assignment_reflected_immediately(app):
    with app.app_context():
        from app.services import department_service

        dept = department_service.create_department("QA팀")
        user = user_service.create_user(name="테스터")
        user_service.set_department(user, dept.id)
        assert user.department_id == dept.id
        assert user.department.name == "QA팀"
