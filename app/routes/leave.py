from datetime import date

from flask import Blueprint, request, redirect, url_for, flash, jsonify

from app.decorators import login_required
from app.services import leave_service

bp = Blueprint("leave", __name__)


@bp.route("/leaves", methods=["POST"])
@login_required
def create():
    form = request.form
    try:
        leave_service.create_leave(
            user_id=request.current_user.id,
            leave_type=form.get("leave_type", "annual"),
            start_date=date.fromisoformat(form.get("start_date")),
            end_date=date.fromisoformat(form.get("end_date")),
            reason=form.get("reason") or None,
        )
        flash("휴무를 등록했습니다.")
    except ValueError as e:
        flash(f"휴무 등록 실패: {e}")
    return redirect(url_for("schedule.page"))


@bp.route("/leaves/<int:leave_id>/delete", methods=["POST"])
@login_required
def delete(leave_id):
    ok = leave_service.delete_leave(leave_id, request.current_user.id)
    flash("휴무를 삭제했습니다." if ok else "본인의 휴무만 삭제할 수 있습니다.")
    return redirect(url_for("schedule.page"))


# ---- API ----

@bp.route("/api/leaves")
@login_required
def api_list():
    rows = leave_service.list_my_leaves(request.current_user.id)
    return jsonify({"leaves": [r.to_dict() for r in rows]})


@bp.route("/api/leaves", methods=["POST"])
@login_required
def api_create():
    payload = request.get_json(silent=True) or {}
    try:
        row = leave_service.create_leave(
            user_id=request.current_user.id,
            leave_type=payload.get("leave_type", "annual"),
            start_date=date.fromisoformat(payload["start_date"]),
            end_date=date.fromisoformat(payload["end_date"]),
            reason=payload.get("reason"),
        )
        return jsonify({"leave": row.to_dict()}), 201
    except (ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/leaves/<int:leave_id>", methods=["PUT"])
@login_required
def api_update(leave_id):
    row = leave_service.get_my_leave_or_none(leave_id, request.current_user.id)
    if not row:
        return jsonify({"error": "본인의 휴무만 수정할 수 있습니다."}), 403
    payload = request.get_json(silent=True) or {}
    if "leave_type" in payload:
        row.leave_type = payload["leave_type"]
    if "start_date" in payload:
        row.start_date = date.fromisoformat(payload["start_date"])
    if "end_date" in payload:
        row.end_date = date.fromisoformat(payload["end_date"])
    if "reason" in payload:
        row.reason = payload["reason"]
    from app.extensions import db
    db.session.commit()
    return jsonify({"leave": row.to_dict()})


@bp.route("/api/leaves/<int:leave_id>", methods=["DELETE"])
@login_required
def api_delete(leave_id):
    ok = leave_service.delete_leave(leave_id, request.current_user.id)
    if not ok:
        return jsonify({"error": "본인의 휴무만 삭제할 수 있습니다."}), 403
    return jsonify({"ok": True})
