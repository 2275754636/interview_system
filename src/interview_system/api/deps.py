"""Dependency injection for FastAPI。"""

from __future__ import annotations

import secrets

from fastapi import Header, Request

from interview_system.api.exceptions import APIError
from interview_system.application.services.admin_service import AdminService
from interview_system.application.services.interview_service import InterviewService
from interview_system.application.services.session_service import SessionService
from interview_system.config.settings import Settings
from interview_system.domain.services.answer_processor import AnswerProcessor
from interview_system.domain.services.followup_generator import FollowupGenerator
from interview_system.infrastructure.cache.memory_cache import SessionCache
from interview_system.infrastructure.database.connection import AsyncDatabase
from interview_system.infrastructure.database.repositories.admin_repository_impl import (
    AdminRepositoryImpl,
)
from interview_system.infrastructure.database.repositories.session_repository_impl import (
    SessionRepositoryImpl,
)


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_database(request: Request) -> AsyncDatabase:
    return request.app.state.db


def get_session_cache(request: Request) -> SessionCache:
    return request.app.state.session_cache


def get_session_repository(request: Request) -> SessionRepositoryImpl:
    db = get_database(request)
    cache = get_session_cache(request)
    return SessionRepositoryImpl(db, cache=cache)


def require_admin_token(
    request: Request,
    x_admin_token: str | None = Header(default=None, alias="X-Admin-Token"),
) -> None:
    settings = get_settings(request)
    configured = (settings.admin_token or "").strip()
    if not configured:
        raise APIError(
            code="ADMIN_DISABLED",
            message="Admin endpoints disabled",
            status_code=404,
        )

    provided = (x_admin_token or "").strip()
    if not provided or not secrets.compare_digest(provided, configured):
        raise APIError(
            code="ADMIN_UNAUTHORIZED",
            message="Unauthorized",
            status_code=401,
        )


def get_admin_repository(request: Request) -> AdminRepositoryImpl:
    db = get_database(request)
    return AdminRepositoryImpl(db)


def get_admin_service(request: Request) -> AdminService:
    repo = get_admin_repository(request)
    return AdminService(repo)


def get_session_service(request: Request) -> SessionService:
    repo = get_session_repository(request)
    return SessionService(repo)


def get_interview_service(request: Request) -> InterviewService:
    from interview_system.common.config import INTERVIEW_CONFIG
    from interview_system.core.questions import EDU_TYPES, SCENES, TOPICS
    from interview_system.integrations.api_helpers import generate_followup

    class _LLM:
        def generate_followup(self, answer: str, topic: dict, conversation_log=None):
            try:
                return generate_followup(answer, topic, conversation_log)
            except Exception:
                return None

    repo = get_session_repository(request)

    processor = AnswerProcessor(
        depth_keywords=INTERVIEW_CONFIG.depth_keywords,
        common_keywords=INTERVIEW_CONFIG.common_keywords,
        max_depth_score=INTERVIEW_CONFIG.max_depth_score,
    )

    followup = FollowupGenerator(
        llm=_LLM(),
        min_answer_length=INTERVIEW_CONFIG.min_answer_length,
        max_followups_per_question=INTERVIEW_CONFIG.max_followups_per_question,
        max_depth_score=INTERVIEW_CONFIG.max_depth_score,
    )

    return InterviewService(
        repository=repo,
        answer_processor=processor,
        followup_generator=followup,
        topics_source={"TOPICS": TOPICS, "SCENES": SCENES, "EDU_TYPES": EDU_TYPES},
        total_questions=INTERVIEW_CONFIG.total_questions,
    )
