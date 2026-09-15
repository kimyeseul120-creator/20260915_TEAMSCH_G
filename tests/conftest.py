import pytest
from sqlalchemy.pool import StaticPool

from app import create_app
from app.config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
    }
    INITIAL_ADMIN_CODE = "ADMIN001"
    INITIAL_ADMIN_NAME = "테스트관리자"


@pytest.fixture
def app():
    return create_app(TestConfig)


@pytest.fixture
def client(app):
    return app.test_client()
