"""共享测试 fixtures。"""

from __future__ import annotations

import pytest

from interview_system.application.services.interview_service import InterviewService
from interview_system.domain.entities import Session
from interview_system.domain.services.answer_processor import AnswerProcessor
from interview_system.domain.services.followup_generator import FollowupGenerator
from interview_system.domain.value_objects.conversation_entry import ConversationEntry


class FakeRepo:
    """内存仓储 mock。"""

    def __init__(self):
        self.sessions: dict[str, Session] = {}
        self.logs: dict[str, list[ConversationEntry]] = {}

    async def get(self, session_id):  # type: ignore[override]
        return self.sessions.get(str(session_id))

    async def save(self, session: Session) -> None:  # type: ignore[override]
        self.sessions[str(session.id)] = session

    async def delete(self, session_id):  # type: ignore[override]
        self.sessions.pop(str(session_id), None)
        self.logs.pop(str(session_id), None)
        return True

    async def list_conversation_entries(self, session_id):  # type: ignore[override]
        return list(self.logs.get(str(session_id), []))

    async def append_conversation_entry(
        self, session_id, entry: ConversationEntry
    ) -> None:  # type: ignore[override]
        self.logs.setdefault(str(session_id), []).append(entry)

    async def delete_last_conversation_entry(self, session_id):  # type: ignore[override]
        items = self.logs.get(str(session_id), [])
        if not items:
            return None
        return items.pop()


@pytest.fixture
def fake_repo() -> FakeRepo:
    """提供 FakeRepo 实例。"""
    return FakeRepo()


@pytest.fixture
def topics_source() -> dict:
    """提供测试用 topics 数据。"""
    return {
        "TOPICS": [
            {
                "name": "学校-德育",
                "scene": "学校",
                "edu_type": "德育",
                "questions": ["Q1"],
                "followups": ["F1"],
            },
            {
                "name": "家庭-智育",
                "scene": "家庭",
                "edu_type": "智育",
                "questions": ["Q2"],
                "followups": ["F2"],
            },
            {
                "name": "社区-体育",
                "scene": "社区",
                "edu_type": "体育",
                "questions": ["Q3"],
                "followups": ["F3"],
            },
            {
                "name": "学校-美育",
                "scene": "学校",
                "edu_type": "美育",
                "questions": ["Q4"],
                "followups": ["F4"],
            },
            {
                "name": "家庭-劳育",
                "scene": "家庭",
                "edu_type": "劳育",
                "questions": ["Q5"],
                "followups": ["F5"],
            },
            {
                "name": "社区-德育",
                "scene": "社区",
                "edu_type": "德育",
                "questions": ["Q6"],
                "followups": ["F6"],
            },
        ],
        "SCENES": ["学校", "家庭", "社区"],
        "EDU_TYPES": ["德育", "智育", "体育", "美育", "劳育"],
    }


@pytest.fixture
def interview_service(fake_repo: FakeRepo, topics_source: dict) -> InterviewService:
    """提供 InterviewService 实例。"""
    processor = AnswerProcessor(
        depth_keywords=["具体"], common_keywords=[], max_depth_score=4
    )
    followup = FollowupGenerator(
        llm=None, min_answer_length=10, max_followups_per_question=3, max_depth_score=4
    )
    return InterviewService(
        repository=fake_repo,  # type: ignore[arg-type]
        answer_processor=processor,
        followup_generator=followup,
        topics_source=topics_source,
        total_questions=2,
    )
