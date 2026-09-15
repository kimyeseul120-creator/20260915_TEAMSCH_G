from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.decorators import login_required
from app.models import TASK_STATUSES
from app.services import task_service

bp = Blueprint("task", __name__)


@bp.route("/tasks")
@login_required
def page():
    view = request.args.get("view", "mine")
    if view == "team":
        status = request.args.get("status")
        tasks = task_service.list_team_tasks(status=status)
    else:
        tasks = task_service.list_my_tasks(request.current_user.id)
    return render_template("task/list.html", tasks=tasks, view=view, task_statuses=TASK_STATUSES)


@bp.route("/tasks", methods=["POST"])
@login_required
def create():
    form = request.form
    try:
        task_service.create_task(
            user_id=request.current_user.id,
            title=form.get("title", ""),
            description=form.get("description") or None,
            status=form.get("status", "planned"),
            progress=form.get("progress", 0),
            priority=form.get("priority", "normal"),
            start_date=date.fromisoformat(form["start_date"]) if form.get("start_date") else None,
            due_date=date.fromisoformat(form["due_date"]) if form.get("due_date") else None,
            project_name=form.get("project_name") or None,
        )
        flash("업무를 등록했습니다.")
    except ValueError as e:
        flash(f"업무 등록 실패: {e}")
    return redirect(url_for("task.page"))


@bp.route("/tasks/<int:task_id>", methods=["POST"])
@login_required
def update(task_id):
    form = request.form
    fields = {
        "title": form.get("title"),
        "description": form.get("description"),
        "status": form.get("status"),
        "progress": form.get("progress", type=int),
        "priority": form.get("priority"),
        "project_name": form.get("project_name"),
    }
    if form.get("due_date"):
        fields["due_date"] = date.fromisoformat(form["due_date"])
    try:
        task = task_service.update_task(task_id, request.current_user.id, **fields)
        flash("업무를 수정했습니다." if task else "본인의 업무만 수정할 수 있습니다.")
    except ValueError as e:
        flash(str(e))
    return redirect(url_for("task.page"))


@bp.route("/tasks/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    ok = task_service.delete_task(task_id, request.current_user.id)
    flash("업무를 삭제했습니다." if ok else "본인의 업무만 삭제할 수 있습니다.")
    return redirect(url_for("task.page"))


# ---- API ----

@bp.route("/api/tasks")
@login_required
def api_list():
    view = request.args.get("view", "mine")
    if view == "team":
        rows = task_service.list_team_tasks(status=request.args.get("status"))
    else:
        rows = task_service.list_my_tasks(request.current_user.id)
    return jsonify({"tasks": [t.to_dict() for t in rows]})


@bp.route("/api/tasks/<int:task_id>")
@login_required
def api_get(task_id):
    from app.models import Task
    task = Task.query.get_or_404(task_id)
    return jsonify({"task": task.to_dict()})


@bp.route("/api/tasks", methods=["POST"])
@login_required
def api_create():
    payload = request.get_json(silent=True) or {}
    try:
        task = task_service.create_task(
            user_id=request.current_user.id,
            title=payload.get("title", ""),
            description=payload.get("description"),
            status=payload.get("status", "planned"),
            progress=payload.get("progress", 0),
            priority=payload.get("priority", "normal"),
            start_date=date.fromisoformat(payload["start_date"]) if payload.get("start_date") else None,
            due_date=date.fromisoformat(payload["due_date"]) if payload.get("due_date") else None,
            project_name=payload.get("project_name"),
        )
        return jsonify({"task": task.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/tasks/<int:task_id>", methods=["PUT"])
@login_required
def api_update(task_id):
    payload = request.get_json(silent=True) or {}
    if "due_date" in payload and payload["due_date"]:
        payload["due_date"] = date.fromisoformat(payload["due_date"])
    try:
        task = task_service.update_task(task_id, request.current_user.id, **payload)
        if not task:
            return jsonify({"error": "본인의 업무만 수정할 수 있습니다."}), 403
        return jsonify({"task": task.to_dict()})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def api_delete(task_id):
    ok = task_service.delete_task(task_id, request.current_user.id)
    if not ok:
        return jsonify({"error": "본인의 업무만 삭제할 수 있습니다."}), 403
    return jsonify({"ok": True})
