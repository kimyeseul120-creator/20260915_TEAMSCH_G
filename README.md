# Team Schedule — 팀원 일정 공유 시스템

사용자코드(비밀번호 없음)로 로그인하는 Flask 기반 팀 일정/근무상태/업무/메모 공유 시스템입니다.
요청서의 요구사항 문서를 기준으로 Phase 1~7(+8 일부)을 구현했습니다.

## 빠른 시작

```bash
pip install -r requirements.txt
cp .env.example .env    # 필요시 값 수정
python run.py
```

브라우저에서 http://127.0.0.1:5050 접속.

**최초 로그인**: DB가 비어있으면 앱이 처음 시작될 때 부트스트랩 관리자 계정을 자동으로 만듭니다.
- 사용자코드: `.env`의 `INITIAL_ADMIN_CODE` (기본값 `ADMIN001`)
- 이 코드로 로그인 후, **사용자 관리** 메뉴에서 실제 팀원 계정을 만들고, 필요하면 부트스트랩 코드를 변경/비활성화하세요.

## 구현된 기능 (요청서 대응)

| 요구사항 | 구현 위치 |
|---|---|
| 사용자코드 로그인 / 비밀번호 없음 | `app/services/auth_service.py`, `app/routes/auth.py` |
| 존재하지 않는/비활성 사용자 로그인 차단 | `auth_service.authenticate()` |
| 로그인 Rate Limit | `auth_service.is_rate_limited()` (IP+코드 기준 in-memory) |
| 관리자/조직원 권한 구분, `@login_required`/`@admin_required` | `app/decorators.py` |
| 사용자 생성/수정/코드변경/부서지정/활성화/비활성화/삭제 | `app/services/user_service.py`, `app/routes/admin.py` |
| **마지막 관리자 보호** | `user_service.set_role/set_active/delete_user` |
| 부서 생성/수정/삭제/활성화 | `app/services/department_service.py` |
| 일정(미팅 포함) CRUD, 참석자, 월간 캘린더 | `app/services/schedule_service.py`, `app/routes/schedule.py`, `templates/schedule/list.html` |
| 근무 상태(🟢🔵🟡🟣🔴🟠) | `app/services/work_status_service.py` |
| 휴무 관리 | `app/services/leave_service.py` |
| 업무/진행률 | `app/services/task_service.py` |
| **개인 메모 (본인만 조회, 관리자도 예외 없음, 서버 소유권 검증, 404 응답)** | `app/services/memo_service.py`, `app/routes/memo.py` |
| 전체 팀원 대시보드(공개), 검색/필터 | `app/services/dashboard_service.py`, `templates/dashboard/index.html` |
| 실시간(폴링) 갱신 | `dashboard/index.html`의 `fetch` + `REFRESH_INTERVAL`(기본 10초) |
| 팀원 상세(공개 정보만, 개인 메모 미노출) | `templates/users/detail.html` |
| CSRF 방어 | Flask-WTF `CSRFProtect`, 모든 폼에 `csrf_token` 포함 |
| 세션 보안(HttpOnly, SameSite, 만료시간) | `app/config.py` |

## 테스트

```bash
pytest
```

특히 `tests/test_memo_security.py`는 요청서 33절이 "반드시" 요구한 개인 메모 IDOR 방지를 검증합니다:
본인 CRUD 가능 / 타인 조회·수정·삭제 차단 / **관리자도 타인 메모 조회 불가** / 목록에 본인 것만 노출.

## 아직 미구현·향후 과제 (Phase 8-9 일부)

- WebSocket/SSE 실시간 반영 (현재는 10초 폴링으로 Phase 8의 1차 구현만 적용)
- Alembic 기반 마이그레이션 (`migrations/` 폴더는 자리만 있음, 현재는 `db.create_all()`로 스키마 생성)
- 캘린더 주간/일간 보기, 드래그앤드롭 (현재는 월간 그리드 + 목록)
- 참석자 알림, 미팅 초대 수락/거절 UI (모델/DB는 준비됨, 화면 미구현)
- 완전한 테스트 커버리지 (일정/업무/부서 CRUD의 happy-path는 서비스 단에서 검증 가능한 구조이나, 인증·마지막 관리자 보호·개인 메모 보안 등 요청서가 "필수"로 못박은 항목 위주로 작성)

## 배포

로컬 SQLite(`team_schedule.db`)가 기본이며, `.env`에 `DATABASE_URL`(Supabase 등 Postgres)을 설정하면
자동으로 전환됩니다. Vercel 배포 시에는 이전 프로젝트(ETNS_TODO_APP)와 동일하게 `vercel.json` +
`DATABASE_URL` 환경변수 방식을 그대로 적용할 수 있습니다 (다만 세션 기반 로그인이므로 서버리스 환경에서는
세션 저장소를 DB/Redis 등으로 옮기는 것을 권장합니다 — 현재는 Flask 기본 쿠키 세션).
