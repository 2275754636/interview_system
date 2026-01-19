"""后台监管（审计/研究）仓储接口。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AdminSessionRow:
    session_id: str
    user_name: str
    start_time: str
    end_time: str | None
    is_finished: bool
    current_question_idx: int
    selected_topics_json: str | None
    created_at: str | None
    updated_at: str | None
    is_followup: bool
    current_followup_is_ai: bool
    current_followup_count: int
    current_followup_question: str


@dataclass(frozen=True, slots=True)
class AdminConversationRow:
    id: int
    session_id: str
    user_name: str
    timestamp: str
    topic: str
    question_type: str
    question: str
    answer: str
    depth_score: int
    is_ai_generated: bool


@dataclass(frozen=True, slots=True)
class AdminTimeSeriesPoint:
    bucket: str
    sessions: int
    messages: int
    unique_users: int
    avg_depth_score: float


@dataclass(frozen=True, slots=True)
class AdminUserActivityRow:
    user_name: str
    sessions: int
    messages: int


@dataclass(frozen=True, slots=True)
class AdminTopicRow:
    topic: str
    messages: int
    avg_depth_score: float


class AdminRepository(Protocol):
    async def list_sessions(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        user_name: str | None,
        is_finished: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[AdminSessionRow]]: ...

    async def search_conversations(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        user_name: str | None,
        topic: str | None,
        keyword: str | None,
        min_depth: int | None,
        max_depth: int | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[AdminConversationRow]]: ...

    async def get_time_series(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        bucket: str,
    ) -> list[AdminTimeSeriesPoint]: ...

    async def get_user_activity(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[AdminUserActivityRow]: ...

    async def get_top_topics(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[AdminTopicRow]: ...

