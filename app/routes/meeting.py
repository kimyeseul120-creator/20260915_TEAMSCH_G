from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort

from app.decorators import login_required
from app.models import User
from app.services import meeting_service
from app.services.meeting_service import SummarizeError

bp = Blueprint("meeting", __name__)


@bp.route("/meetings")
@login_required
def list_page():
    view = request.args.get("view", "mine")
    if view == "all":
        meetings = meeting_service.list_meetings()
    else:
        meetings = meeting_service.list_my_meetings(request.current_user)
    users = (
        User.query.filter(User.is_active.is_(True), User.id != request.current_user.id)
        .order_by(User.name)
        .all()
    )
    return render_template("meeting/list.html", meetings=meetings, view=view, users=users)


@bp.route("/meetings", methods=["POST"])
@login_required
def create():
    title = request.form.get("title", "")
    participant_ids = [int(x) for x in request.form.getlist("participant_ids") if x]
    meeting = meeting_service.create_meeting(request.current_user.id, title, participant_ids)
    return redirect(url_for("meeting.room", meeting_id=meeting.id))


@bp.route("/meetings/<int:meeting_id>")
@login_required
def room(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        abort(404)
    if not meeting.is_member(request.current_user):
        flash("초대받은 회의가 아닙니다. 개설자에게 초대를 요청해주세요.")
        return redirect(url_for("meeting.list_page"))

    summary_lines = meeting_service.parse_summary_lines(meeting.summary) if meeting.summary else []
    invited_ids = meeting.invited_user_ids() | {meeting.created_by}
    invitable_users = (
        User.query.filter(User.is_active.is_(True), ~User.id.in_(invited_ids))
        .order_by(User.name)
        .all()
    )
    can_manage = request.current_user.is_admin or request.current_user.id == meeting.created_by
    return render_template(
        "meeting/room.html",
        meeting=meeting,
        summary_lines=summary_lines,
        invitable_users=invitable_users,
        can_manage=can_manage,
    )


@bp.route("/meetings/<int:meeting_id>/invite", methods=["POST"])
@login_required
def invite(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        abort(404)
    if not (request.current_user.is_admin or request.current_user.id == meeting.created_by):
        flash("회의를 개설한 사람만 참여자를 초대할 수 있습니다.")
        return redirect(url_for("meeting.room", meeting_id=meeting_id))

    user_ids = [int(x) for x in request.form.getlist("invite_ids") if x]
    if not user_ids:
        flash("초대할 팀원을 선택해주세요.")
        return redirect(url_for("meeting.room", meeting_id=meeting_id))

    added = meeting_service.invite_participants(meeting_id, user_ids, request.current_user.id)
    flash(f"{added}명을 회의에 초대했습니다." if added else "이미 초대된 팀원입니다.")
    return redirect(url_for("meeting.room", meeting_id=meeting_id))


@bp.route("/meetings/<int:meeting_id>/participants/<int:user_id>/remove", methods=["POST"])
@login_required
def remove_participant(meeting_id, user_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        abort(404)
    if not (request.current_user.is_admin or request.current_user.id == meeting.created_by):
        flash("회의를 개설한 사람만 참여자를 제외할 수 있습니다.")
        return redirect(url_for("meeting.room", meeting_id=meeting_id))
    meeting_service.remove_participant(meeting_id, user_id)
    flash("참여자를 초대 목록에서 제외했습니다.")
    return redirect(url_for("meeting.room", meeting_id=meeting_id))


@bp.route("/meetings/<int:meeting_id>/messages", methods=["POST"])
@login_required
def send_message(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting or not meeting.is_member(request.current_user):
        abort(404)
    try:
        meeting_service.add_message(meeting_id, request.current_user.id, request.form.get("content", ""))
    except ValueError as e:
        flash(str(e))
    return redirect(url_for("meeting.room", meeting_id=meeting_id))


@bp.route("/meetings/<int:meeting_id>/close", methods=["POST"])
@login_required
def close(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        abort(404)
    if meeting.created_by != request.current_user.id and not request.current_user.is_admin:
        flash("회의를 개설한 사람만 종료할 수 있습니다.")
        return redirect(url_for("meeting.room", meeting_id=meeting_id))
    meeting_service.close_meeting(meeting_id)
    flash("회의를 종료했습니다.")
    return redirect(url_for("meeting.room", meeting_id=meeting_id))


@bp.route("/meetings/<int:meeting_id>/summarize", methods=["POST"])
@login_required
def summarize(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting or not meeting.is_member(request.current_user):
        abort(404)
    try:
        meeting_service.generate_summary(meeting_id)
        flash("회의 내용을 정리했습니다.")
    except SummarizeError as e:
        flash(str(e))
    return redirect(url_for("meeting.room", meeting_id=meeting_id))


# ---- API (채팅 실시간 폴링) ----

@bp.route("/api/meetings/<int:meeting_id>/messages")
@login_required
def api_messages(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting or not meeting.is_member(request.current_user):
        abort(404)
    after_id = request.args.get("after_id", type=int, default=0)
    rows = meeting_service.messages_since(meeting_id, after_id)
    return jsonify({
        "messages": [r.to_dict() for r in rows],
        "is_closed": meeting.is_closed,
    })
