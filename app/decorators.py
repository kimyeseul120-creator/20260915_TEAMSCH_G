from functools import wraps

from flask import session, redirect, url_for, flash, jsonify, request

from app.models import User


def get_current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = User.query.get(user_id)
    if not user or not user.is_active:
        return None
    return user


def _reject_unauthenticated():
    session.clear()
    if request.path.startswith("/api/"):
        return jsonify({"error": "로그인이 필요합니다."}), 401
    flash("로그인이 필요합니다.")
    return redirect(url_for("auth.login"))


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _reject_unauthenticated()
        request.current_user = user
        return view(*args, **kwargs)

    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = get_current_user()
        if not user:
            return _reject_unauthenticated()
        if not user.is_admin:
            if request.path.startswith("/api/"):
                return jsonify({"error": "관리자 권한이 필요합니다."}), 403
            flash("관리자 권한이 필요합니다.")
            return redirect(url_for("dashboard.index"))
        request.current_user = user
        return view(*args, **kwargs)

    return wrapped
