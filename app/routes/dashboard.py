from flask import Blueprint, render_template, jsonify, request, current_app

from app.decorators import login_required
from app.models import Department
from app.services import dashboard_service

bp = Blueprint("dashboard", __name__)


@bp.route("/")
@login_required
def index():
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    return render_template(
        "dashboard/index.html",
        departments=departments,
        refresh_interval=current_app.config["REFRESH_INTERVAL"],
    )


@bp.route("/api/dashboard/summary")
@login_required
def api_summary():
    return jsonify(dashboard_service.summary())


@bp.route("/api/dashboard/team-status")
@login_required
def api_team_status():
    department_id = request.args.get("department_id", type=int)
    status = request.args.get("status")
    keyword = request.args.get("q")
    rows = dashboard_service.team_status(department_id=department_id, status=status, keyword=keyword)
    return jsonify({"rows": rows})
