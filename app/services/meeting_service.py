"""
온라인 회의(채팅) 서비스.

참여자끼리 채팅으로 회의를 진행하고, 채팅 내용을 Groq API로 아래 계층 구조에
맞춰 자동 정리한다. 개설자는 특정 팀원을 회의에 초대할 수 있다.

1. 대제목
□ 소제목
- 세부내용
· 하위내용
"""
import os
import re
from datetime import datetime

from app.extensions import db
from app.models import OnlineMeeting, MeetingMessage, MeetingParticipant


def list_meetings():
    return OnlineMeeting.query.order_by(OnlineMeeting.created_at.desc()).all()


def list_my_meetings(user):
    """내가 개설했거나 초대받은 회의 (관리자는 전체)."""
    all_meetings = list_meetings()
    if user and user.is_admin:
        return all_meetings
    return [m for m in all_meetings if m.is_member(user)]


def get_meeting(meeting_id):
    return OnlineMeeting.query.get(meeting_id)


def create_meeting(user_id, title, participant_ids=None):
    title = (title or "").strip() or "제목 없는 회의"
    meeting = OnlineMeeting(title=title, created_by=user_id)
    db.session.add(meeting)
    db.session.flush()  # meeting.id 확보

    for uid in set(participant_ids or []):
        if uid and uid != user_id:
            db.session.add(
                MeetingParticipant(meeting_id=meeting.id, user_id=uid, invited_by=user_id)
            )

    db.session.commit()
    return meeting


def invite_participants(meeting_id, user_ids, invited_by):
    """이미 만들어진 회의에 참여자를 추가로 초대한다. 새로 추가된 인원 수를 반환."""
    meeting = OnlineMeeting.query.get(meeting_id)
    if not meeting:
        raise ValueError("존재하지 않는 회의입니다.")

    existing_ids = meeting.invited_user_ids()
    added = 0
    for uid in set(user_ids or []):
        if uid and uid != meeting.created_by and uid not in existing_ids:
            db.session.add(
                MeetingParticipant(meeting_id=meeting_id, user_id=uid, invited_by=invited_by)
            )
            added += 1
    db.session.commit()
    return added


def remove_participant(meeting_id, user_id):
    row = MeetingParticipant.query.filter_by(meeting_id=meeting_id, user_id=user_id).first()
    if not row:
        return False
    db.session.delete(row)
    db.session.commit()
    return True


def add_message(meeting_id, user_id, content):
    content = (content or "").strip()
    if not content:
        raise ValueError("메시지 내용을 입력해주세요.")
    meeting = OnlineMeeting.query.get(meeting_id)
    if not meeting:
        raise ValueError("존재하지 않는 회의입니다.")
    if meeting.is_closed:
        raise ValueError("종료된 회의에는 메시지를 보낼 수 없습니다.")
    msg = MeetingMessage(meeting_id=meeting_id, user_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    return msg


def import_from_meeting(target_meeting_id, source_meeting_id, user):
    """
    지난 회의(source)의 내용을 지금 진행 중인 회의(target)로 끌어와, 참고용 채팅
    메시지로 남긴다. 정리된 요약이 있으면 요약을, 없으면 대화 원문을 가져온다.
    두 회의 모두에 접근 권한(is_member)이 있는 경우에만 허용한다.
    """
    target = OnlineMeeting.query.get(target_meeting_id)
    source = OnlineMeeting.query.get(source_meeting_id)
    if not target or not source:
        raise ValueError("회의를 찾을 수 없습니다.")
    if target.id == source.id:
        raise ValueError("같은 회의에서는 불러올 수 없습니다.")
    if not target.is_member(user) or not source.is_member(user):
        raise ValueError("접근 권한이 있는 회의만 불러올 수 있습니다.")
    if target.is_closed:
        raise ValueError("종료된 회의에는 내용을 가져올 수 없습니다.")

    if source.summary:
        body = source.summary
    elif source.messages:
        body = "\n".join(
            f"{m.user.name if m.user else '알수없음'}: {m.content}" for m in source.messages
        )
    else:
        raise ValueError("불러올 채팅 내용이나 정리된 요약이 없는 회의입니다.")

    content = f"📋 [지난 회의 '{source.title}' 내용 가져옴]\n{body}"
    msg = MeetingMessage(meeting_id=target_meeting_id, user_id=user.id, content=content)
    db.session.add(msg)
    db.session.commit()
    return msg


def messages_since(meeting_id, after_id=0):
    return (
        MeetingMessage.query.filter(
            MeetingMessage.meeting_id == meeting_id, MeetingMessage.id > after_id
        )
        .order_by(MeetingMessage.id.asc())
        .all()
    )


def close_meeting(meeting_id):
    meeting = OnlineMeeting.query.get(meeting_id)
    if meeting:
        meeting.is_closed = True
        db.session.commit()
    return meeting


class SummarizeError(Exception):
    pass


SUMMARY_SYSTEM_PROMPT = """당신은 회의록 정리 보조원입니다. 주어진 회의 채팅 내용을 아래 계층 구조로만, 한국어로 정리하세요.

1. 대제목
□ 소제목
- 세부내용
· 하위내용

규칙:
- 반드시 위 4단계 기호(숫자+마침표, □, -, ·)만 사용해서 들여쓰기 없이 각 줄 맨 앞에 붙인다.
- 대제목(1. 2. 3. ...)은 회의에서 다룬 주요 주제 단위로 나눈다.
- 인사말, 잡담처럼 회의 내용과 무관한 발언은 제외한다.
- 참여자 목록이나 다른 안내 문구는 출력하지 말고, 정리된 내용만 출력한다.
- 실제로 나온 내용만 정리하고 없는 내용을 지어내지 않는다.
"""


def generate_summary(meeting_id):
    """
    Groq API(무료 요금제, 신용카드 등록 불필요)로 채팅 내용을 요약한다.
    console.groq.com에서 발급받은 GROQ_API_KEY 환경변수가 필요하다.
    """
    meeting = OnlineMeeting.query.get(meeting_id)
    if not meeting:
        raise SummarizeError("회의를 찾을 수 없습니다.")
    if not meeting.messages:
        raise SummarizeError("정리할 채팅 내용이 없습니다.")

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise SummarizeError(
            "GROQ_API_KEY가 설정되어 있지 않습니다. console.groq.com에서 무료로 발급받아 "
            ".env 파일(로컬) 또는 Vercel 환경변수에 추가해주세요."
        )

    try:
        from groq import Groq
    except ImportError as exc:
        raise SummarizeError(
            "groq 패키지가 설치되어 있지 않습니다. requirements.txt를 다시 설치해주세요."
        ) from exc

    transcript = "\n".join(
        f"{m.user.name if m.user else '알수없음'}: {m.content}" for m in meeting.messages
    )

    client = Groq(api_key=api_key)
    model = os.environ.get("SUMMARY_MODEL", "llama-3.1-8b-instant")

    try:
        resp = client.chat.completions.create(
            model=model,
            max_tokens=1500,
            messages=[
                {"role": "system", "content": SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": f"[회의 제목: {meeting.title}]\n\n{transcript}"},
            ],
        )
        body = (resp.choices[0].message.content or "").strip()
    except Exception as exc:  # noqa: BLE001 - 외부 API 호출 실패를 사용자 메시지로 변환
        hint = ""
        if "model_not_found" in str(exc) or "does not exist" in str(exc):
            hint = (
                " (모델을 찾을 수 없습니다. console.groq.com/docs/models 에서 사용 가능한 "
                "모델명을 확인해 SUMMARY_MODEL 환경변수에 설정해보세요.)"
            )
        raise SummarizeError(f"요약 생성 중 오류가 발생했습니다: {exc}{hint}") from exc

    participants = meeting.participant_names()
    participants_line = "참여자: " + (", ".join(participants) if participants else "-")

    meeting.summary = f"{participants_line}\n\n{body}"
    meeting.summarized_at = datetime.utcnow()
    db.session.commit()
    return meeting


_LEVEL1 = re.compile(r"^\d+\.\s*")


def parse_summary_lines(text):
    """저장된 요약 텍스트를 (level, text) 목록으로 변환해 화면에 계층별로 렌더링할 수 있게 한다."""
    lines = []
    for raw in (text or "").split("\n"):
        line = raw.strip()
        if not line:
            continue
        if _LEVEL1.match(line):
            lines.append({"level": 1, "text": line})
        elif line.startswith("□"):
            lines.append({"level": 2, "text": line})
        elif line.startswith("·"):
            lines.append({"level": 4, "text": line})
        elif line.startswith("-"):
            lines.append({"level": 3, "text": line})
        else:
            lines.append({"level": 0, "text": line})
    return lines
