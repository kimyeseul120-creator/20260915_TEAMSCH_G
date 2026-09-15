from datetime import datetime, date, time

from app.models import User, WorkStatus, Schedule, Leave, Task, STATUS_CHOICES


def _today_range():
    today = date.today()
    start = datetime.combine(today, time.min)
    end = datetime.combine(today, time.max)
    return start, end


def summary():
    today_start, today_end = _today_range()
    today = date.today()

    active_users = User.query.filter_by(is_active=True).all()
    total_members = len(active_users)

    # 근무 상태를 아직 한 번도 설정하지 않은 사용자는 기본값 "근무중"으로 집계한다
    # (팀원 현황 목록의 기본 표시값과 일치시키기 위함).
    status_by_user = {
        row.user_id: row.status
        for row in WorkStatus.query.join(User).filter(User.is_active.is_(True)).all()
    }
    status_counts = {key: 0 for key in STATUS_CHOICES}
    for user in active_users:
        current = status_by_user.get(user.id, "working")
        if current in status_counts:
            status_counts[current] += 1

    today_meetings = Schedule.query.filter(
        Schedule.schedule_type == "meeting",
        Schedule.start_datetime <= today_end,
        Schedule.end_datetime >= today_start,
    ).count()

    today_leaves = Leave.query.filter(Leave.start_date <= today, Leave.end_date >= today).count()

    ongoing_tasks = Task.query.filter(Task.status == "in_progress").count()

    return {
        "total_members": total_members,
        "working": status_counts.get("working", 0),
        "remote": status_counts.get("remote", 0),
        "outside": status_counts.get("outside", 0),
        "business_trip": status_counts.get("business_trip", 0),
        "vacation": status_counts.get("vacation", 0),
        "today_meetings": today_meetings,
        "today_leaves": today_leaves,
        "ongoing_tasks": ongoing_tasks,
    }


def team_status(department_id=None, status=None, keyword=None):
    today_start, today_end = _today_range()

    query = User.query.filter_by(is_active=True)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(User.name.ilike(like))

    rows = []
    for user in query.order_by(User.name.asc()).all():
        ws = WorkStatus.query.filter_by(user_id=user.id).first()
        current_status = ws.status if ws else "working"
        if status and current_status != status:
            continue

        next_schedule = (
            Schedule.query.filter(
                Schedule.created_by == user.id,
                Schedule.start_datetime <= today_end,
                Schedule.end_datetime >= today_start,
            )
            .order_by(Schedule.start_datetime.asc())
            .first()
        )
        current_task = (
            Task.query.filter_by(user_id=user.id, status="in_progress")
            .order_by(Task.updated_at.desc())
            .first()
        )

        rows.append({
            "id": user.id,
            "name": user.name,
            "department": user.department.name if user.department else "-",
            "status": current_status,
            "status_label": STATUS_CHOICES.get(current_status, current_status),
            "today_schedule": next_schedule.title if next_schedule else None,
            "task_title": current_task.title if current_task else None,
            "task_progress": current_task.progress if current_task else None,
        })
    return rows
