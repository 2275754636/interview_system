"""Session management routes"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime
from typing import List
import uuid

from ..schemas.session import SessionCreate, SessionResponse, SessionStats
from ..schemas.message import MessageCreate, MessageResponse
from ..deps import get_session_manager
from interview_system.core.interview_engine import InterviewEngine
from interview_system.services.session_manager import SessionManager


router = APIRouter(prefix="/session", tags=["session"])

UNDO_STACK_MAX = 10


def _capture_session_state(session) -> dict:
    return {
        "session_id": session.session_id,
        "current_question_idx": session.current_question_idx,
        "is_finished": session.is_finished,
        "end_time": session.end_time,
        "is_followup": session.is_followup,
        "current_followup_is_ai": session.current_followup_is_ai,
        "current_followup_count": session.current_followup_count,
        "current_followup_question": session.current_followup_question,
    }


def _push_undo_snapshot(session) -> None:
    snapshot = {
        "log_count_before": len(session.conversation_log),
        "session_state_before": _capture_session_state(session),
    }
    session.undo_stack.append(snapshot)
    session.undo_stack = session.undo_stack[-UNDO_STACK_MAX:]


def _is_message_entry(msg: dict) -> bool:
    if not isinstance(msg, dict):
        return False
    role = msg.get("role")
    content = msg.get("content")
    return role in {"user", "assistant", "system"} and isinstance(content, str) and content.strip() != ""


def _to_message_responses(conversation_log: List[dict]) -> List[MessageResponse]:
    message_entries = [m for m in conversation_log if _is_message_entry(m)]
    return [
        _to_message_response(msg, f"msg_{i}")
        for i, msg in enumerate(message_entries)
    ]


def _to_session_response(session) -> SessionResponse:
    """Convert InterviewSession to API response"""
    status = "completed" if session.is_finished else "active"

    created_timestamp = int(
        datetime.strptime(session.start_time, "%Y-%m-%d %H:%M:%S").timestamp() * 1000
    ) if session.start_time else int(datetime.now().timestamp() * 1000)

    return SessionResponse(
        id=session.session_id,
        status=status,
        current_question=session.current_question_idx,
        total_questions=len(session.selected_topics) if session.selected_topics else 0,
        created_at=created_timestamp,
        user_name=session.user_name
    )


def _to_message_response(msg: dict, msg_id: str = None) -> MessageResponse:
    """Convert conversation log entry to API response"""
    timestamp = msg.get("timestamp", datetime.now().timestamp())
    if isinstance(timestamp, str):
        timestamp = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").timestamp()

    return MessageResponse(
        id=msg_id or f"msg_{uuid.uuid4().hex[:8]}",
        role=msg.get("role", "assistant"),
        content=msg.get("content", ""),
        timestamp=int(timestamp * 1000)
    )


@router.post("/start", response_model=SessionResponse)
async def start_session(
    data: SessionCreate,
    manager: SessionManager = Depends(get_session_manager)
):
    """Create new interview session"""
    session = manager.create_session(user_name=data.user_name)

    # Initialize engine to select questions
    engine = InterviewEngine(session)

    # Get first question
    first_question = engine.get_current_question()
    if first_question:
        session.conversation_log.append({
            "role": "assistant",
            "content": first_question,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        manager.update_session(session)

    return _to_session_response(session)


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Get session details"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _to_session_response(session)


@router.post("/{session_id}/message", response_model=MessageResponse)
async def send_message(
    session_id: str,
    data: MessageCreate,
    manager: SessionManager = Depends(get_session_manager)
):
    """Process user message and get AI response"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.is_finished:
        raise HTTPException(status_code=400, detail="Session already completed")

    _push_undo_snapshot(session)

    # Log user message
    session.conversation_log.append({
        "role": "user",
        "content": data.text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    # Process answer through engine
    engine = InterviewEngine(session)
    result = engine.process_answer(data.text)

    # Determine response content
    if result.is_finished:
        response_content = result.message or "访谈已结束，感谢您的参与！"
    elif result.need_followup:
        response_content = result.followup_question
    else:
        response_content = result.next_question or result.message

    # Log assistant response
    session.conversation_log.append({
        "role": "assistant",
        "content": response_content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    manager.update_session(session)

    return _to_message_response(
        {"role": "assistant", "content": response_content},
        f"msg_{uuid.uuid4().hex[:8]}"
    )


@router.get("/{session_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Get all messages in session"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return _to_message_responses(session.conversation_log)


@router.post("/{session_id}/undo", response_model=List[MessageResponse])
async def undo_message(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Undo last exchange (user + assistant messages)"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not session.undo_stack:
        raise HTTPException(status_code=400, detail="No messages to undo")

    snapshot = session.undo_stack.pop()
    target_log_count = int(snapshot.get("log_count_before", 0))
    session_state = snapshot.get("session_state_before", {})

    ok = manager.rollback_session(
        session_id,
        target_log_count=target_log_count,
        session_state=session_state
    )
    if not ok:
        raise HTTPException(status_code=500, detail="Undo failed")

    return _to_message_responses(session.conversation_log)


@router.post("/{session_id}/skip", response_model=MessageResponse)
async def skip_question(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Skip current question and move to next"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.is_finished:
        raise HTTPException(status_code=400, detail="Session already completed")

    _push_undo_snapshot(session)

    engine = InterviewEngine(session)

    # Move to next question
    if not session.is_followup:
        session.current_question_idx += 1
    else:
        session.is_followup = False
        session.current_followup_count = 0
        session.current_question_idx += 1

    next_question = engine.get_current_question()

    if not next_question:
        session.is_finished = True
        response_content = "访谈已结束，感谢您的参与！"
    else:
        response_content = next_question

    session.conversation_log.append({
        "role": "assistant",
        "content": response_content,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    manager.update_session(session)

    return _to_message_response(
        {"role": "assistant", "content": response_content},
        f"msg_{uuid.uuid4().hex[:8]}"
    )


@router.post("/{session_id}/restart", response_model=SessionResponse)
async def restart_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Reset session to beginning"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Reset state
    session.current_question_idx = 0
    session.is_followup = False
    session.current_followup_count = 0
    session.current_followup_question = ""
    session.is_finished = False
    session.conversation_log = []
    session.undo_stack = []

    # Get first question
    engine = InterviewEngine(session)
    first_question = engine.get_current_question()

    if first_question:
        session.conversation_log.append({
            "role": "assistant",
            "content": first_question,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    manager.update_session(session)

    return _to_session_response(session)


@router.get("/{session_id}/stats", response_model=SessionStats)
async def get_stats(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Get session statistics"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    message_entries = [m for m in session.conversation_log if _is_message_entry(m)]
    user_msgs = [m for m in message_entries if m.get("role") == "user"]
    assistant_msgs = [m for m in message_entries if m.get("role") == "assistant"]

    # Calculate duration
    start = datetime.strptime(session.start_time, "%Y-%m-%d %H:%M:%S")
    end = datetime.strptime(session.end_time, "%Y-%m-%d %H:%M:%S") if session.end_time else datetime.now()
    duration = int((end - start).total_seconds())

    # Estimate average response time (simplified)
    avg_response_time = duration / max(len(user_msgs), 1)

    return SessionStats(
        total_messages=len(message_entries),
        user_messages=len(user_msgs),
        assistant_messages=len(assistant_msgs),
        average_response_time=round(avg_response_time, 2),
        duration_seconds=duration
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    manager: SessionManager = Depends(get_session_manager)
):
    """Delete session"""
    session = manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    ok = manager.delete_session(session_id)
    if not ok:
        raise HTTPException(status_code=500, detail="Failed to delete session")

    return {"status": "deleted", "session_id": session_id}
