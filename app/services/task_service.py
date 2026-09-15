from app.extensions import db
from app.models import Task, TASK_STATUSES


def list_my_tasks(user_id):
    return Task.query.filter_by(user_id=user_id).order_by(Task.updated_at.desc()).all()


def list_team_tasks(status=None):
    query = Task.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Task.updated_at.desc()).all()


def get_my_task_or_none(task_id, user_id):
    return Task.query.filter_by(id=task_id, user_id=user_id).first()


def create_task(user_id, title, description=None, status="planned", progress=0,
                 priority="normal", start_date=None, due_date=None, project_name=None):
    if status not in TASK_STATUSES:
        raise ValueError("올바르지 않은 업무 상태입니다.")
    progress = max(0, min(100, int(progress or 0)))
    task = Task(
        user_id=user_id, title=title.strip(), description=description,
        status=status, progress=progress, priority=priority,
        start_date=start_date, due_date=due_date, project_name=project_name,
    )
    db.session.add(task)
    db.session.commit()
    return task


def update_task(task_id, user_id, **fields):
    task = get_my_task_or_none(task_id, user_id)
    if not task:
        return None
    if "title" in fields and fields["title"]:
        task.title = fields["title"].strip()
    if "description" in fields:
        task.description = fields["description"]
    if "status" in fields and fields["status"]:
        if fields["status"] not in TASK_STATUSES:
            raise ValueError("올바르지 않은 업무 상태입니다.")
        task.status = fields["status"]
        if task.status == "done":
            task.progress = 100
    if "progress" in fields and fields["progress"] is not None:
        task.progress = max(0, min(100, int(fields["progress"])))
    if "priority" in fields:
        task.priority = fields["priority"]
    if "due_date" in fields:
        task.due_date = fields["due_date"]
    if "project_name" in fields:
        task.project_name = fields["project_name"]
    db.session.commit()
    return task


def delete_task(task_id, user_id):
    task = get_my_task_or_none(task_id, user_id)
    if not task:
        return False
    db.session.delete(task)
    db.session.commit()
    return True
