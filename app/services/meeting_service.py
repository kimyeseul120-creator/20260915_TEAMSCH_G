"""
온라인 회의(채팅) 서비스.

참여자끼리 채팅으로 회의를 진행하고, 채팅 내용을 Claude API로 아래 계층 구조에
맞춰 자동 정리한다.

1. 대제목
□ 소제목
- 세부내용
· 하위내용
"""
import os
import re
from datetime import datetime

from app.extensions import db
from app.models import OnlineMeeting, MeetingMessage


def list_meetings():
    return OnlineMeeting.query.order_by(OnlineMeeting.created_at.desc()).all()


def get_meeting(meeting_id):
    return OnlineMeeting.query.get(meeting_id)


def create_meeting(user_id, title):
    title = (title or "").strip() or "제목 없는 회의"
    meeting = OnlineMeeting(title=title, created_by=user_id)
    db.session.add(meeting)
    db.session.commit()
    return meeting


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
    meeting = OnlineMeeting.query.get(meeting_id)
    if not meeting:
        raise SummarizeError("회의를 찾을 수 없습니다.")
    if not meeting.messages:
        raise SummarizeError("정리할 채팅 내용이 없습니다.")

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise SummarizeError(
            "ANTHROPIC_API_KEY가 설정되어 있지 않습니다. .env 파일(로컬) 또는 Vercel 환경변수에 추가해주세요."
        )

    try:
        import anthropic
    except ImportError as exc:
        raise SummarizeError(
            "anthropic 패키지가 설치되어 있지 않습니다. requirements.txt를 다시 설치해주세요."
        ) from exc

    transcript = "\n".join(
        f"{m.user.name if m.user else '알수없음'}: {m.content}" for m in meeting.messages
    )

    client = anthropic.Anthropic(api_key=api_key)
    model = os.environ.get("SUMMARY_MODEL", "claude-sonnet-5")

    try:
        resp = client.messages.create(
            model=model,
            max_tokens=1500,
            system=SUMMARY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": f"[회의 제목: {meeting.title}]\n\n{transcript}"}],
        )
        body = "".join(block.text for block in resp.content if block.type == "text").strip()
    except Exception as exc:  # noqa: BLE001 - 외부 API 호출 실패를 사용자 메시지로 변환
        raise SummarizeError(f"요약 생성 중 오류가 발생했습니다: {exc}") from exc

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
