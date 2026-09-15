import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "team-schedule-dev-secret-key")

    _database_url = os.environ.get("DATABASE_URL")
    if _database_url:
        # Supabase 등에서 주는 postgres:// 형식을 SQLAlchemy가 요구하는 postgresql://로 보정
        if _database_url.startswith("postgres://"):
            _database_url = _database_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = _database_url
    elif os.environ.get("VERCEL"):
        # Vercel 서버리스는 프로젝트 폴더가 읽기 전용이고 /tmp만 쓰기 가능하다.
        # (DATABASE_URL 미설정 시 데이터는 재배포/재시작마다 초기화됨 - Supabase 연결 권장)
        SQLALCHEMY_DATABASE_URI = "sqlite:////tmp/team_schedule.db"
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{BASE_DIR / 'team_schedule.db'}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # 세션 보안
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "false").lower() == "true"
    PERMANENT_SESSION_LIFETIME_MINUTES = int(os.environ.get("SESSION_LIFETIME_MINUTES", "480"))

    # 최초 부트스트랩 관리자 (users 테이블이 비어 있을 때만 자동 생성)
    INITIAL_ADMIN_CODE = os.environ.get("INITIAL_ADMIN_CODE", "ADMIN001")
    INITIAL_ADMIN_NAME = os.environ.get("INITIAL_ADMIN_NAME", "시스템관리자")

    # 대시보드 자동 새로고침 주기 (ms) - Phase 8 실시간 갱신
    REFRESH_INTERVAL = int(os.environ.get("REFRESH_INTERVAL", "10000"))

    # 로그인 Rate Limit
    LOGIN_RATE_LIMIT_MAX = int(os.environ.get("LOGIN_RATE_LIMIT_MAX", "10"))
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("LOGIN_RATE_LIMIT_WINDOW_SECONDS", "300"))

    WTF_CSRF_TIME_LIMIT = None
