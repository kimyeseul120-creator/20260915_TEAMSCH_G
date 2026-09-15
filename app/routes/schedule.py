import calendar as calendar_module
from datetime import datetime, date, time, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.decorators import login_required
from app.models import Schedule, User, SCHEDULE_TYPES
from app.services import schedule_service

bp = Blueprint("schedule", __name__)


def _parse_month(year, month):
    first_day = date(year, month, 1)
    last_day_num = calendar_module.monthrange(year, month)[1]
    last_day = date(year, month, last_day_num)
    return first_day, last_day


@bp.route("/schedule")
@login_required
def page():
    user = request.current_user
    today = date.today()
    year = request.args.get("year", type=int, default=today.year)
    month = request.args.get("month", type=int, default=today.month)
    view = request.args.get("view", "team")  # team(전체) / mine(내 일정)

    first_day, last_day = _parse_month(year, month)
    range_start = datetime.combine(first_day, time.min)
    range_end = datetime.combine(last_day, time.max)

    if view == "mine":
        schedules = schedule_service.list_for_user(user.id, range_start, range_end)
    else:
        schedules = schedule_service.list_for_range(range_start, range_end)

    by_day = {}
    for s in schedules:
        d = s.start_datetime.date()
        by_day.setdefault(d, []).append(s)

    cal = calendar_module.Calendar(firstweekday=6)  # 일요일 시작
    weeks = cal.monthdatescalendar(year, month)

    prev_month = (date(year, month, 1) - timedelta(days=1))
    next_month = (last_day + timedelta(days=1))

    users = User.query.filter_by(is_active=True).order_by(User.name).all()

    return render_template(
        "schedule/list.html",
        year=year, month=month, weeks=weeks, by_day=by_day, today=today,
        view=view, prev_year=prev_month.year, prev_month=prev_month.month,
        next_year=next_month.year, next_month=next_month.month,
        schedule_types=SCHEDULE_TYPES, users=users,
    )


@bp.route("/schedule", methods=["POST"])
@login_required
def create():
    form = request.form
    try:
        start_dt = datetime.fromisoformat(form.get("start_datetime"))
        end_dt = datetime.fromisoformat(form.get("end_datetime"))
        participant_ids = [int(x) for x in form.getlist("participant_ids")]
        schedule_service.create_schedule(
            user_id=request.current_user.id,
            title=form.get("title", ""),
            schedule_type=form.get("schedule_type", "etc"),
            start_datetime=start_dt,
            end_datetime=end_dt,
            description=form.get("description") or None,
            is_all_day=form.get("is_all_day") == "on",
            location=form.get("location") or None,
            meeting_url=form.get("meeting_url") or None,
            participant_ids=participant_ids,
        )
        flash("일정을 등록했습니다.")
    except (ValueError, TypeError) as e:
        flash(f"일정 등록 실패: {e}")
    return redirect(url_for("schedule.page", year=request.form.get("ref_year"), month=request.form.get("ref_month")))


@bp.route("/schedule/<int:schedule_id>/delete", methods=["POST"])
@login_required
def delete(schedule_id):
    ok = schedule_service.delete_schedule(schedule_id, request.current_user.id)
    flash("일정을 삭제했습니다." if ok else "본인이 등록한 일정만 삭제할 수 있습니다.")
    return redirect(url_for("schedule.page"))


# ---- API ----

@bp.route("/api/schedules")
@login_required
def api_list():
    start = request.args.get("start")
    end = request.args.get("end")
    if start and end:
        rows = schedule_service.list_for_range(datetime.fromisoformat(start), datetime.fromisoformat(end))
    else:
        today_start = datetime.combine(date.today(), time.min)
        today_end = datetime.combine(date.today() + timedelta(days=30), time.max)
        rows = schedule_service.list_for_range(today_start, today_end)
    return jsonify({"schedules": [s.to_dict() for s in rows]})


@bp.route("/api/schedules/<int:schedule_id>")
@login_required
def api_get(schedule_id):
    s = Schedule.query.get_or_404(schedule_id)
    return jsonify({"schedule": s.to_dict()})


@bp.route("/api/schedules", methods=["POST"])
@login_required
def api_create():
    payload = request.get_json(silent=True) or {}
    try:
        s = schedule_service.create_schedule(
            user_id=request.current_user.id,
            title=payload.get("title", ""),
            schedule_type=payload.get("schedule_type", "etc"),
            start_datetime=datetime.fromisoformat(payload["start_datetime"]),
            end_datetime=datetime.fromisoformat(payload["end_datetime"]),
            description=payload.get("description"),
            is_all_day=bool(payload.get("is_all_day", False)),
            location=payload.get("location"),
            meeting_url=payload.get("meeting_url"),
            participant_ids=payload.get("participant_ids", []),
        )
        return jsonify({"schedule": s.to_dict()}), 201
    except (ValueError, KeyError) as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/schedules/<int:schedule_id>", methods=["PUT"])
@login_required
def api_update(schedule_id):
    payload = request.get_json(silent=True) or {}
    fields = {}
    for key in ("title", "description", "schedule_type", "location", "meeting_url", "is_all_day"):
        if key in payload:
            fields[key] = payload[key]
    if "start_datetime" in payload:
        fields["start_datetime"] = datetime.fromisoformat(payload["start_datetime"])
    if "end_datetime" in payload:
        fields["end_datetime"] = datetime.fromisoformat(payload["end_datetime"])

    s = schedule_service.update_schedule(schedule_id, request.current_user.id, **fields)
    if not s:
        return jsonify({"error": "본인이 등록한 일정만 수정할 수 있습니다."}), 403
    return jsonify({"schedule": s.to_dict()})


@bp.route("/api/schedules/<int:schedule_id>", methods=["DELETE"])
@login_required
def api_delete(schedule_id):
    ok = schedule_service.delete_schedule(schedule_id, request.current_user.id)
    if not ok:
        return jsonify({"error": "본인이 등록한 일정만 삭제할 수 있습니다."}), 403
    return jsonify({"ok": True})
