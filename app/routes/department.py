from flask import Blueprint, jsonify

from app.decorators import login_required
from app.models import Department

bp = Blueprint("department", __name__)


@bp.route("/api/departments")
@login_required
def api_list_departments():
    departments = Department.query.order_by(Department.name).all()
    return jsonify({"departments": [d.to_dict() for d in departments]})


@bp.route("/api/departments/<int:dept_id>")
@login_required
def api_get_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    return jsonify({"department": dept.to_dict()})
