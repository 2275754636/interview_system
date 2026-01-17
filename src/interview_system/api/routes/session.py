"""Session 路由（薄层）。"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends

from interview_system.api.deps import get_interview_service, get_session_service
from interview_system.api.mappers import to_message_responses, to_session_response
from interview_system.api.schemas.session import (
    SessionCreate,
    SessionResponse,
    SessionStats,
    StartSessionResponse,
)
from interview_system.application.exceptions import SessionNotFoundError
from interview_system.application.services.interview_service import InterviewService
from interview_system.application.services.session_service import SessionService

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/start", response_model=StartSessionResponse)
async def start_session(
    data: SessionCreate, service: InterviewService = Depends(get_interview_service)
):
    session = await service.start_session(user_name=data.user_name, topics=data.topics)
    messages = await service.get_messages(session.id)
    return StartSessionResponse(
        session=to_session_response(session), messages=to_message_responses(messages)
    )


@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: UUID, service: SessionService = Depends(get_session_service)
):
    session = await service.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)
    return to_session_response(session)


@router.post("/{session_id}/restart", response_model=SessionResponse)
async def restart_session(
    session_id: UUID, service: InterviewService = Depends(get_interview_service)
):
    session = await service.restart(session_id=session_id)
    return to_session_response(session)


@router.get("/{session_id}/stats", response_model=SessionStats)
async def get_stats(
    session_id: UUID,
    interview: InterviewService = Depends(get_interview_service),
    session_service: SessionService = Depends(get_session_service),
):
    session = await session_service.get(session_id)
    if session is None:
        raise SessionNotFoundError(session_id)

    messages = await interview.get_messages(session_id)
    user_count = 0
    assistant_count = 0
    for msg in messages:
        role = msg.get("role")
        if role == "user":
            user_count += 1
        elif role == "assistant":
            assistant_count += 1

    duration_seconds = int(
        (datetime.now(timezone.utc) - session.created_at).total_seconds()
    )
    avg_response_time = duration_seconds / user_count if user_count > 0 else 0.0

    return SessionStats(
        total_messages=len(messages),
        user_messages=user_count,
        assistant_messages=assistant_count,
        average_response_time=round(avg_response_time, 2),
        duration_seconds=duration_seconds,
    )


@router.delete("/{session_id}")
async def delete_session(
    session_id: UUID, service: SessionService = Depends(get_session_service)
):
    ok = await service.delete(session_id)
    if not ok:
        raise SessionNotFoundError(session_id)
    return {"status": "deleted", "session_id": str(session_id)}
