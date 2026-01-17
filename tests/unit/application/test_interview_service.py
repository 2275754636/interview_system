"""InterviewService 单元测试。"""

from __future__ import annotations

import pytest

from interview_system.application.services.interview_service import InterviewService


@pytest.mark.asyncio
async def test_interview_service_start_and_get_messages(
    interview_service: InterviewService,
):
    session = await interview_service.start_session(user_name="tester", topics=None)
    assert session.user_name == "tester"
    assert len(session.selected_topics) == 2

    messages = await interview_service.get_messages(session.id)
    assert messages[-1]["role"] == "assistant"
    assert "第1/2题" in messages[-1]["content"]


@pytest.mark.asyncio
async def test_interview_service_followup_then_next_question(
    interview_service: InterviewService,
):
    session = await interview_service.start_session(user_name="tester", topics=None)

    r1 = await interview_service.process_answer(session_id=session.id, answer="短")
    assert r1.is_finished is False
    assert r1.assistant_message in {"F1", "F2", "F3", "F4", "F5", "F6"}

    r2 = await interview_service.process_answer(
        session_id=session.id, answer="足够长的回答内容足够长"
    )
    assert r2.is_finished is False
    assert "第2/2题" in r2.assistant_message


@pytest.mark.asyncio
async def test_interview_service_undo_and_restart(
    interview_service: InterviewService,
):
    session = await interview_service.start_session(user_name="tester", topics=None)

    await interview_service.process_answer(session_id=session.id, answer="短")
    assert await interview_service.get_messages(session.id)

    await interview_service.undo_last(session_id=session.id)
    messages = await interview_service.get_messages(session.id)
    assert messages[-1]["role"] == "assistant"

    await interview_service.restart(session_id=session.id)
    messages2 = await interview_service.get_messages(session.id)
    assert len(messages2) == 1
