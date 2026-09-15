from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort

from app.decorators import login_required
from app.services import meeting_service
from app.services.meeting_service import SummarizeError

bp = Blueprint("meeting", __name__)


@bp.route("/meetings")
@login_required
def list_page():
    meetings = meeting_service.list_meetings()
    return render_template("meeting/list.html", meetings=meetings)


@bp.route("/meetings", methods=["POST"])
@login_required
def create():
    title = request.form.get("title", "")
    meeting = meeting_service.create_meeting(request.current_user.id, title)
    return redirect(url_for("meeting.room", meeting_id=meeting.id))


@bp.route("/meetings/<int:meeting_id>")
@login_required
def room(meeting_id):
    meeting = meeting_service.get_meeting(meeting_id)
    if not meeting:
        abort(404)
    summary_lines = meeting_service.parse_summary_lines(meeting.summary) if meeting.summary else []
    return render_template("meeting/room.html", meeting=meeting, summary_lines=summary_lines)


@bp.route("/meetings/<int:meeting_id>/messages", methods=["POST"])
@login_required
def send_message(meeting_id):
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
    after_id = request.args.get("after_id", type=int, default=0)
    rows = meeting_service.messages_since(meeting_id, after_id)
    meeting = meeting_service.get_meeting(meeting_id)
    return jsonify({
        "messages": [r.to_dict() for r in rows],
        "is_closed": meeting.is_closed if meeting else True,
    })
