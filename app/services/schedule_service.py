from app.extensions import db
from app.models import Schedule, ScheduleParticipant, SCHEDULE_TYPES


def list_for_range(start, end):
    """start~end 구간과 겹치는 전체(공유) 일정을 조회한다."""
    return (
        Schedule.query.filter(Schedule.start_datetime <= end, Schedule.end_datetime >= start)
        .order_by(Schedule.start_datetime.asc())
        .all()
    )


def list_for_user(user_id, start=None, end=None):
    """본인이 만들었거나 참석자로 등록된 일정."""
    query = Schedule.query.outerjoin(ScheduleParticipant).filter(
        db.or_(Schedule.created_by == user_id, ScheduleParticipant.user_id == user_id)
    )
    if start and end:
        query = query.filter(Schedule.start_datetime <= end, Schedule.end_datetime >= start)
    return query.order_by(Schedule.start_datetime.asc()).distinct().all()


def get_owned_or_none(schedule_id, user_id):
    return Schedule.query.filter_by(id=schedule_id, created_by=user_id).first()


def create_schedule(user_id, title, schedule_type, start_datetime, end_datetime,
                     description=None, is_all_day=False, location=None,
                     meeting_url=None, participant_ids=None):
    if schedule_type not in SCHEDULE_TYPES:
        raise ValueError("올바르지 않은 일정 유형입니다.")
    if end_datetime < start_datetime:
        raise ValueError("종료 시각은 시작 시각보다 빠를 수 없습니다.")

    schedule = Schedule(
        title=title.strip(), description=description, schedule_type=schedule_type,
        start_datetime=start_datetime, end_datetime=end_datetime, is_all_day=is_all_day,
        location=location, meeting_url=meeting_url, created_by=user_id,
    )
    db.session.add(schedule)
    db.session.flush()  # schedule.id 확보

    for uid in set(participant_ids or []):
        db.session.add(ScheduleParticipant(schedule_id=schedule.id, user_id=uid))

    db.session.commit()
    return schedule


def update_schedule(schedule_id, user_id, **fields):
    schedule = get_owned_or_none(schedule_id, user_id)
    if not schedule:
        return None
    for key in ("title", "description", "schedule_type", "start_datetime",
                "end_datetime", "is_all_day", "location", "meeting_url"):
        if key in fields and fields[key] is not None:
            setattr(schedule, key, fields[key])
    db.session.commit()
    return schedule


def delete_schedule(schedule_id, user_id):
    schedule = get_owned_or_none(schedule_id, user_id)
    if not schedule:
        return False
    db.session.delete(schedule)
    db.session.commit()
    return True
