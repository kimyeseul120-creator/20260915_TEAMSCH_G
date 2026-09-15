"""
인증 서비스.

- 사용자코드만으로 로그인 (비밀번호 없음)
- 존재하지 않거나 비활성화된 사용자는 로그인 불가
- 간단한 in-memory Rate Limit (IP + 사용자코드 기준, 단일 프로세스 기준 동작)

향후 사용자코드+비밀번호 또는 SSO로 확장할 때는 authenticate() 시그니처만
바꾸면 되도록, 인증 로직을 이 모듈 하나로 분리해두었다.
"""
import time
from collections import defaultdict, deque

from flask import current_app

from app.models import User

_login_attempts = defaultdict(deque)


def _key(remote_addr, user_code):
    return f"{remote_addr}:{user_code}"


def is_rate_limited(remote_addr, user_code):
    max_attempts = current_app.config["LOGIN_RATE_LIMIT_MAX"]
    window = current_app.config["LOGIN_RATE_LIMIT_WINDOW_SECONDS"]
    now = time.time()
    attempts = _login_attempts[_key(remote_addr, user_code)]
    while attempts and now - attempts[0] > window:
        attempts.popleft()
    return len(attempts) >= max_attempts


def record_login_attempt(remote_addr, user_code):
    _login_attempts[_key(remote_addr, user_code)].append(time.time())


def authenticate(user_code):
    """사용자코드로 로그인 시도. (user, error_message) 튜플을 반환한다."""
    if not user_code:
        return None, "사용자코드를 입력해주세요."

    user = User.query.filter_by(user_code=user_code).first()
    if not user:
        return None, "등록되지 않은 사용자코드입니다."
    if not user.is_active:
        return None, "비활성화된 사용자입니다.\n관리자에게 문의해주세요."
    return user, None


def count_active_admins(exclude_user_id=None):
    query = User.query.filter_by(role="admin", is_active=True)
    if exclude_user_id is not None:
        query = query.filter(User.id != exclude_user_id)
    return query.count()
