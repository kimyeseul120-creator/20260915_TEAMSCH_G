import os
from pathlib import Path

try:
    # 로컬 실행 시 .env 파일의 값을 os.environ으로 자동으로 읽어온다.
    # (Vercel 등 배포 환경에서는 대시보드에서 직접 환경변수를 설정하므로 이 파일이 없어도 무방)
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


def _int_env(name, default):
    """환경변수가 아예 없거나 빈 문자열("")인 경우 모두 default를 쓴다.
    (Vercel 등에서 값 없이 키만 등록되면 os.environ.get()이 빈 문자열을 반환해
    int() 변환이 실패하는 문제를 방지)"""
    value = os.environ.get(name)
    if value is None or value.strip() == "":
        return default
    return int(value)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "team-schedule-dev-secret-key"

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
    PERMANENT_SESSION_LIFETIME_MINUTES = _int_env("SESSION_LIFETIME_MINUTES", 480)

    # 최초 부트스트랩 관리자 (users 테이블이 비어 있을 때만 자동 생성)
    INITIAL_ADMIN_CODE = os.environ.get("INITIAL_ADMIN_CODE") or "ADMIN001"
    INITIAL_ADMIN_NAME = os.environ.get("INITIAL_ADMIN_NAME") or "시스템관리자"

    # 대시보드 자동 새로고침 주기 (ms) - Phase 8 실시간 갱신
    REFRESH_INTERVAL = _int_env("REFRESH_INTERVAL", 10000)

    # 로그인 Rate Limit
    LOGIN_RATE_LIMIT_MAX = _int_env("LOGIN_RATE_LIMIT_MAX", 10)
    LOGIN_RATE_LIMIT_WINDOW_SECONDS = _int_env("LOGIN_RATE_LIMIT_WINDOW_SECONDS", 300)

    WTF_CSRF_TIME_LIMIT = None
