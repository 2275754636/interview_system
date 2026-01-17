"""InterviewService 单元测试。"""

from __future__ import annotations

import asyncio
import time

import pytest

from interview_system.application.services.interview_service import InterviewService
from interview_system.domain.services.answer_processor import AnswerProcessor
from interview_system.domain.services.followup_generator import FollowupGenerator


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


class SlowLLM:
    def generate_followup(self, answer: str, topic: dict, conversation_log=None):  # type: ignore[override]
        time.sleep(0.2)
        return None


@pytest.mark.asyncio
async def test_interview_service_followup_generation_does_not_block_event_loop(
    fake_repo, topics_source
):
    processor = AnswerProcessor(
        depth_keywords=["具体"], common_keywords=[], max_depth_score=4
    )
    followup = FollowupGenerator(
        llm=SlowLLM(), min_answer_length=10, max_followups_per_question=3, max_depth_score=4
    )
    service = InterviewService(
        repository=fake_repo,  # type: ignore[arg-type]
        answer_processor=processor,
        followup_generator=followup,
        topics_source=topics_source,
        total_questions=2,
    )

    session = await service.start_session(user_name="tester", topics=None)

    tick = asyncio.Event()

    async def ticker() -> None:
        await asyncio.sleep(0.02)
        tick.set()

    ticker_task = asyncio.create_task(ticker())
    process_task = asyncio.create_task(service.process_answer(session_id=session.id, answer="短"))

    await asyncio.wait_for(tick.wait(), timeout=0.1)
    await process_task
    await ticker_task
