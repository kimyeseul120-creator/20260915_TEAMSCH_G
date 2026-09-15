from flask import Blueprint, request, redirect, url_for, flash, jsonify

from app.decorators import login_required
from app.models import STATUS_CHOICES
from app.services import work_status_service

bp = Blueprint("work_status", __name__)


@bp.route("/work-status", methods=["POST"])
@login_required
def update():
    status = request.form.get("status")
    memo = request.form.get("memo") or None
    try:
        work_status_service.set_status(request.current_user.id, status, memo)
        flash("현재 상태를 변경했습니다.")
    except ValueError as e:
        flash(str(e))
    return redirect(request.referrer or url_for("dashboard.index"))


@bp.route("/api/work-status")
@login_required
def api_get():
    row = work_status_service.get_status(request.current_user.id)
    return jsonify({"status": row.to_dict() if row else None, "choices": STATUS_CHOICES})


@bp.route("/api/work-status", methods=["PUT"])
@login_required
def api_update():
    payload = request.get_json(silent=True) or {}
    try:
        row = work_status_service.set_status(request.current_user.id, payload.get("status"), payload.get("memo"))
        return jsonify({"status": row.to_dict()})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
