from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify

from app.decorators import get_current_user, login_required
from app.services.auth_service import authenticate, is_rate_limited, record_login_attempt

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if get_current_user():
            return redirect(url_for("dashboard.index"))
        return render_template("auth/login.html")

    user_code = request.form.get("user_code", "").strip().upper()
    remote_addr = request.remote_addr or "unknown"

    if is_rate_limited(remote_addr, user_code):
        flash("로그인 시도가 너무 많습니다. 잠시 후 다시 시도해주세요.")
        return redirect(url_for("auth.login"))

    record_login_attempt(remote_addr, user_code)

    user, error = authenticate(user_code)
    if error:
        flash(error)
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return redirect(url_for("dashboard.index"))


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


# ---- JSON API (스펙 27절) ----

@bp.route("/api/auth/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    user_code = (payload.get("user_code") or "").strip().upper()
    remote_addr = request.remote_addr or "unknown"

    if is_rate_limited(remote_addr, user_code):
        return jsonify({"error": "로그인 시도가 너무 많습니다."}), 429
    record_login_attempt(remote_addr, user_code)

    user, error = authenticate(user_code)
    if error:
        return jsonify({"error": error}), 401

    session.clear()
    session["user_id"] = user.id
    session.permanent = True
    return jsonify({"user": user.to_dict()})


@bp.route("/api/auth/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"ok": True})


@bp.route("/api/auth/me")
@login_required
def api_me():
    return jsonify({"user": request.current_user.to_dict(include_private=True)})
