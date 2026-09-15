from datetime import datetime, date, time

from flask import Blueprint, render_template, jsonify, request, abort

from app.decorators import login_required
from app.models import User, WorkStatus, Schedule, Task, STATUS_CHOICES

bp = Blueprint("user", __name__)


@bp.route("/members/<int:user_id>")
@login_required
def detail(user_id):
    """
    팀원 상세(공개) 화면. 개인 메모 등 개인 전용 정보는 절대 포함하지 않는다 (요구사항 21).
    """
    member = User.query.filter_by(id=user_id, is_active=True).first_or_404()

    ws = WorkStatus.query.filter_by(user_id=member.id).first()
    status = ws.status if ws else "working"

    today_start = datetime.combine(date.today(), time.min)
    today_end = datetime.combine(date.today(), time.max)
    today_schedules = (
        Schedule.query.filter(
            Schedule.created_by == member.id,
            Schedule.start_datetime <= today_end,
            Schedule.end_datetime >= today_start,
        )
        .order_by(Schedule.start_datetime.asc())
        .all()
    )
    current_task = (
        Task.query.filter_by(user_id=member.id, status="in_progress")
        .order_by(Task.updated_at.desc())
        .first()
    )

    return render_template(
        "users/detail.html",
        member=member,
        status_label=STATUS_CHOICES.get(status, status),
        today_schedules=today_schedules,
        current_task=current_task,
    )


# ---- API (읽기 전용 - 조직원도 조회 가능한 기본 목록) ----

@bp.route("/api/users")
@login_required
def api_list_users():
    users = User.query.order_by(User.name).all()
    return jsonify({"users": [u.to_dict() for u in users]})


@bp.route("/api/users/<int:user_id>")
@login_required
def api_get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify({"user": user.to_dict()})
