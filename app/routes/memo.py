"""
개인 메모 라우트.

요구사항 22/23/29/32: 개인 메모는 작성자 본인만 조회할 수 있고, 관리자를 포함해
그 누구도 다른 사람의 메모를 볼 수 없다. 이를 프론트엔드에서 숨기는 방식이 아니라
반드시 서버(이 라우트 + memo_service)에서 user_id 소유권을 검증해 차단한다.
다른 사람의 메모 id로 접근하면 403이 아니라 404를 반환해 존재 여부 자체를 숨긴다.
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort

from app.decorators import login_required
from app.services import memo_service

bp = Blueprint("memo", __name__)


@bp.route("/memos")
@login_required
def page():
    keyword = request.args.get("q", "").strip()
    memos = memo_service.list_my_memos(request.current_user.id, keyword=keyword or None)
    return render_template("memo/list.html", memos=memos, keyword=keyword)


@bp.route("/memos", methods=["POST"])
@login_required
def create():
    try:
        memo_service.create_memo(
            request.current_user.id, request.form.get("title", ""), request.form.get("content", "")
        )
        flash("메모를 저장했습니다.")
    except ValueError as e:
        flash(str(e))
    return redirect(url_for("memo.page"))


@bp.route("/memos/<int:memo_id>", methods=["POST"])
@login_required
def update(memo_id):
    memo = memo_service.update_memo(
        memo_id, request.current_user.id,
        title=request.form.get("title"), content=request.form.get("content"),
    )
    if not memo:
        abort(404)
    flash("메모를 수정했습니다.")
    return redirect(url_for("memo.page"))


@bp.route("/memos/<int:memo_id>/delete", methods=["POST"])
@login_required
def delete(memo_id):
    ok = memo_service.delete_memo(memo_id, request.current_user.id)
    if not ok:
        abort(404)
    flash("메모를 삭제했습니다.")
    return redirect(url_for("memo.page"))


# ---- API ----

@bp.route("/api/memos")
@login_required
def api_list():
    keyword = request.args.get("q")
    memos = memo_service.list_my_memos(request.current_user.id, keyword=keyword)
    return jsonify({"memos": [m.to_dict() for m in memos]})


@bp.route("/api/memos/<int:memo_id>")
@login_required
def api_get(memo_id):
    memo = memo_service.get_my_memo_or_none(memo_id, request.current_user.id)
    if not memo:
        abort(404)
    return jsonify({"memo": memo.to_dict()})


@bp.route("/api/memos", methods=["POST"])
@login_required
def api_create():
    payload = request.get_json(silent=True) or {}
    try:
        memo = memo_service.create_memo(
            request.current_user.id, payload.get("title", ""), payload.get("content", "")
        )
        return jsonify({"memo": memo.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@bp.route("/api/memos/<int:memo_id>", methods=["PUT"])
@login_required
def api_update(memo_id):
    payload = request.get_json(silent=True) or {}
    memo = memo_service.update_memo(
        memo_id, request.current_user.id, title=payload.get("title"), content=payload.get("content")
    )
    if not memo:
        abort(404)
    return jsonify({"memo": memo.to_dict()})


@bp.route("/api/memos/<int:memo_id>", methods=["DELETE"])
@login_required
def api_delete(memo_id):
    ok = memo_service.delete_memo(memo_id, request.current_user.id)
    if not ok:
        abort(404)
    return jsonify({"ok": True})
