from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify

from app.decorators import admin_required
from app.models import User, Department
from app.services import user_service, department_service
from app.services.user_service import UserServiceError
from app.services.department_service import DepartmentServiceError

bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------- 사용자 관리 화면 ----------------

@bp.route("/users")
@admin_required
def users_page():
    keyword = request.args.get("q", "").strip()
    department_id = request.args.get("department_id", type=int)
    role = request.args.get("role")
    status = request.args.get("status")

    query = User.query
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(User.user_code.ilike(like) | User.name.ilike(like))
    if department_id:
        query = query.filter(User.department_id == department_id)
    if role:
        query = query.filter(User.role == role)
    if status == "active":
        query = query.filter(User.is_active.is_(True))
    elif status == "inactive":
        query = query.filter(User.is_active.is_(False))

    users = query.order_by(User.name).all()
    departments = Department.query.order_by(Department.name).all()
    return render_template("users/list.html", users=users, departments=departments,
                            keyword=keyword, selected_department=department_id,
                            selected_role=role, selected_status=status)


@bp.route("/users", methods=["POST"])
@admin_required
def create_user():
    form = request.form
    try:
        user_service.create_user(
            user_code=form.get("user_code", ""),
            name=form.get("name", ""),
            department_id=form.get("department_id", type=int),
            position=form.get("position") or None,
            email=form.get("email") or None,
            phone=form.get("phone") or None,
            role=form.get("role", "member"),
            is_active=form.get("is_active") == "on",
        )
        flash("사용자를 생성했습니다.")
    except UserServiceError as e:
        flash(str(e))
    return redirect(url_for("admin.users_page"))


@bp.route("/users/<int:user_id>", methods=["POST"])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = request.form
    action = form.get("action", "update")

    try:
        if action == "update":
            user_service.update_user(
                user, name=form.get("name"), position=form.get("position"),
                email=form.get("email"), phone=form.get("phone"),
                department_id=form.get("department_id", type=int),
            )
            flash("사용자 정보를 수정했습니다.")
        elif action == "change_code":
            user_service.change_user_code(user, form.get("user_code", ""))
            flash("사용자코드를 변경했습니다.")
        elif action == "set_department":
            user_service.set_department(user, form.get("department_id", type=int))
            flash("부서를 변경했습니다.")
        elif action == "set_role":
            user_service.set_role(user, form.get("role", "member"))
            flash("권한을 변경했습니다.")
        elif action == "activate":
            user_service.set_active(user, True)
            flash("사용자를 활성화했습니다.")
        elif action == "deactivate":
            user_service.set_active(user, False)
            flash("사용자를 비활성화했습니다.")
        elif action == "delete":
            user_service.delete_user(user)
            flash("사용자를 삭제했습니다.")
    except UserServiceError as e:
        flash(str(e))

    return redirect(url_for("admin.users_page"))


# ---------------- 부서 관리 화면 ----------------

@bp.route("/departments")
@admin_required
def departments_page():
    departments = Department.query.order_by(Department.name).all()
    return render_template("departments/list.html", departments=departments)


@bp.route("/departments", methods=["POST"])
@admin_required
def create_department():
    try:
        department_service.create_department(
            name=request.form.get("name", ""),
            description=request.form.get("description") or None,
        )
        flash("부서를 생성했습니다.")
    except DepartmentServiceError as e:
        flash(str(e))
    return redirect(url_for("admin.departments_page"))


@bp.route("/departments/<int:dept_id>", methods=["POST"])
@admin_required
def update_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    action = request.form.get("action", "update")
    try:
        if action == "update":
            department_service.update_department(
                dept, name=request.form.get("name"), description=request.form.get("description")
            )
            flash("부서 정보를 수정했습니다.")
        elif action == "activate":
            department_service.set_active(dept, True)
        elif action == "deactivate":
            department_service.set_active(dept, False)
        elif action == "delete":
            department_service.delete_department(dept)
            flash("부서를 삭제했습니다.")
    except DepartmentServiceError as e:
        flash(str(e))
    return redirect(url_for("admin.departments_page"))


# ---------------- 관리자 전용 JSON API (스펙 28절) ----------------

@bp.route("/api/admin/users", methods=["POST"])
@admin_required
def api_create_user():
    payload = request.get_json(silent=True) or {}
    try:
        user = user_service.create_user(**{
            k: payload.get(k) for k in
            ("user_code", "name", "department_id", "position", "email", "phone", "role", "is_active")
            if k in payload
        })
        return jsonify({"user": user.to_dict()}), 201
    except UserServiceError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/admin/users/<int:user_id>", methods=["PUT"])
@admin_required
def api_update_user(user_id):
    user = User.query.get_or_404(user_id)
    payload = request.get_json(silent=True) or {}
    try:
        if "role" in payload:
            user_service.set_role(user, payload["role"])
        if "is_active" in payload:
            user_service.set_active(user, bool(payload["is_active"]))
        if "user_code" in payload:
            user_service.change_user_code(user, payload["user_code"])
        user_service.update_user(
            user, name=payload.get("name"), position=payload.get("position"),
            email=payload.get("email"), phone=payload.get("phone"),
            department_id=payload.get("department_id"),
        )
        return jsonify({"user": user.to_dict()})
    except UserServiceError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/admin/users/<int:user_id>", methods=["DELETE"])
@admin_required
def api_delete_user(user_id):
    user = User.query.get_or_404(user_id)
    try:
        user_service.delete_user(user)
        return jsonify({"ok": True})
    except UserServiceError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/admin/departments", methods=["POST"])
@admin_required
def api_create_department():
    payload = request.get_json(silent=True) or {}
    try:
        dept = department_service.create_department(payload.get("name"), payload.get("description"))
        return jsonify({"department": dept.to_dict()}), 201
    except DepartmentServiceError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/admin/departments/<int:dept_id>", methods=["PUT"])
@admin_required
def api_update_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    payload = request.get_json(silent=True) or {}
    try:
        department_service.update_department(dept, payload.get("name"), payload.get("description"))
        return jsonify({"department": dept.to_dict()})
    except DepartmentServiceError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/admin/departments/<int:dept_id>", methods=["DELETE"])
@admin_required
def api_delete_department(dept_id):
    dept = Department.query.get_or_404(dept_id)
    try:
        department_service.delete_department(dept)
        return jsonify({"ok": True})
    except DepartmentServiceError as e:
        return jsonify({"error": str(e)}), 400
