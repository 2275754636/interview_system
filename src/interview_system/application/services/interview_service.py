"""访谈应用服务：编排领域服务与状态持久化。"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from interview_system.application.dto.interview_dto import InterviewResultDTO
from interview_system.application.exceptions import (
    NothingToUndoError,
    SessionAlreadyCompletedError,
    SessionNotFoundError,
)
from interview_system.domain.entities.session import Session, SessionStatus
from interview_system.domain.repositories.session_repository import SessionRepository
from interview_system.domain.services.answer_processor import AnswerProcessor
from interview_system.domain.services.followup_generator import FollowupGenerator
from interview_system.domain.services.question_selector import select_questions
from interview_system.domain.value_objects.conversation_entry import ConversationEntry


class InterviewService:
    """访谈用例编排。"""

    def __init__(
        self,
        *,
        repository: SessionRepository,
        answer_processor: AnswerProcessor,
        followup_generator: FollowupGenerator,
        topics_source: dict[str, Any],
        total_questions: int,
    ) -> None:
        self._repository = repository
        self._answer_processor = answer_processor
        self._followup_generator = followup_generator
        self._topics_source = topics_source
        self._total_questions = int(total_questions)

    async def start_session(
        self, *, user_name: str | None, topics: list[str] | None = None
    ) -> Session:
        session = Session(user_name=user_name or "访谈者")
        selected = self._select_topics(
            topics=topics, seed=int(session.id.int & 0xFFFFFFFF)
        )
        session.selected_topics = selected
        await self._repository.save(session)
        return session

    async def get_messages(self, session_id: UUID) -> list[dict[str, Any]]:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        entries = await self._repository.list_conversation_entries(session_id)
        messages: list[dict[str, Any]] = []

        for entry in entries:
            ts = int(entry.timestamp.timestamp() * 1000)
            messages.append(
                {"role": "assistant", "content": entry.question, "timestamp": ts}
            )
            messages.append({"role": "user", "content": entry.answer, "timestamp": ts})

        if not session.is_finished():
            messages.append(
                {
                    "role": "assistant",
                    "content": self._current_question_text(session),
                    "timestamp": int(datetime.now(timezone.utc).timestamp() * 1000),
                }
            )

        return messages

    async def process_answer(
        self, *, session_id: UUID, answer: str
    ) -> InterviewResultDTO:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        if session.is_finished():
            raise SessionAlreadyCompletedError(session_id)

        topic = self._get_current_topic(session)
        if topic is None:
            session.finish()
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message="访谈已结束，感谢您的参与！", is_finished=True
            )

        if session.is_followup:
            return await self._process_followup_answer(
                session=session, topic=topic, answer=answer
            )

        return await self._process_core_answer(
            session=session, topic=topic, answer=answer
        )

    async def skip_question(self, *, session_id: UUID) -> InterviewResultDTO:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        if session.is_finished():
            raise SessionAlreadyCompletedError(session_id)

        topic = self._get_current_topic(session)
        if topic is None:
            session.finish()
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message="访谈已结束，感谢您的参与！", is_finished=True
            )

        question_text = self._current_question_text(session)
        entry = ConversationEntry(
            timestamp=datetime.now(timezone.utc),
            topic=str(topic.get("name", "")),
            question_type="追问跳过" if session.is_followup else "核心问题",
            question=question_text,
            answer="用户选择跳过追问" if session.is_followup else "用户选择跳过",
            depth_score=0,
            is_ai_generated=bool(session.current_followup_is_ai),
        )
        await self._repository.append_conversation_entry(session_id, entry)

        # 状态前进
        if session.is_followup:
            session.is_followup = False
            session.current_followup_count = 0
            session.current_followup_question = ""
            session.current_followup_is_ai = False

        session.current_question_idx += 1
        if session.current_question_idx >= self._total_questions:
            session.finish()
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message="访谈已结束，感谢您的参与！", is_finished=True
            )

        await self._repository.save(session)
        return InterviewResultDTO(
            assistant_message=self._current_question_text(session), is_finished=False
        )

    async def undo_last(self, *, session_id: UUID) -> None:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        last = await self._repository.delete_last_conversation_entry(session_id)
        if last is None:
            raise NothingToUndoError(session_id)

        # 退回到“刚刚那道题/追问”处，等待重新回答
        if "追问" in last.question_type:
            session.is_followup = True
            session.current_followup_question = last.question
            session.current_followup_is_ai = bool(last.is_ai_generated)
            session.current_followup_count = max(0, session.current_followup_count - 1)
        else:
            session.current_question_idx = max(0, session.current_question_idx - 1)
            session.is_followup = False
            session.current_followup_is_ai = False
            session.current_followup_count = 0
            session.current_followup_question = ""

        if session.is_finished():
            session.status = SessionStatus.ACTIVE

        await self._repository.save(session)

    async def restart(self, *, session_id: UUID) -> Session:
        session = await self._repository.get(session_id)
        if session is None:
            raise SessionNotFoundError(session_id)

        # 删除全部日志（逐条删除直到空）
        while True:
            deleted = await self._repository.delete_last_conversation_entry(session_id)
            if deleted is None:
                break

        session.current_question_idx = 0
        session.is_followup = False
        session.current_followup_is_ai = False
        session.current_followup_count = 0
        session.current_followup_question = ""
        session.status = SessionStatus.ACTIVE

        await self._repository.save(session)
        return session

    def _select_topics(
        self, *, topics: list[str] | None, seed: int
    ) -> list[dict[str, Any]]:
        all_topics: list[dict[str, Any]] = list(self._topics_source["TOPICS"])
        scenes: list[str] = list(self._topics_source["SCENES"])
        edu_types: list[str] = list(self._topics_source["EDU_TYPES"])

        if topics:
            wanted = {t.strip() for t in topics if t and t.strip()}
            filtered = [t for t in all_topics if str(t.get("name")) in wanted]
            if len(filtered) >= self._total_questions:
                return filtered[: self._total_questions]
            base = select_questions(
                topics=all_topics,
                scenes=scenes,
                edu_types=edu_types,
                total_questions=self._total_questions,
                seed=seed,
            )
            for t in base:
                if t not in filtered:
                    filtered.append(t)
                if len(filtered) >= self._total_questions:
                    break
            return filtered[: self._total_questions]

        return select_questions(
            topics=all_topics,
            scenes=scenes,
            edu_types=edu_types,
            total_questions=self._total_questions,
            seed=seed,
        )

    def _get_current_topic(self, session: Session) -> dict[str, Any] | None:
        idx = session.current_question_idx
        if idx < 0:
            return None
        if idx >= len(session.selected_topics):
            return None
        return session.selected_topics[idx]

    def _format_core_question(self, *, session: Session, topic: dict[str, Any]) -> str:
        idx = session.current_question_idx
        question_text = str((topic.get("questions") or [""])[0])
        return f"【第{idx + 1}/{self._total_questions}题】{topic.get('name', '')}:\n{question_text}"

    def _current_question_text(self, session: Session) -> str:
        if session.is_followup:
            return session.current_followup_question or "能再具体说说吗？"

        topic = self._get_current_topic(session)
        if topic is None:
            return "访谈已结束，感谢您的参与！"
        return self._format_core_question(session=session, topic=topic)

    async def _process_core_answer(
        self, *, session: Session, topic: dict[str, Any], answer: str
    ) -> InterviewResultDTO:
        question_text = self._format_core_question(session=session, topic=topic)
        result = self._answer_processor.process_core_answer(
            answer=answer, topic=topic, question_text=question_text
        )

        entry = ConversationEntry(
            timestamp=result.timestamp,
            topic=result.topic,
            question_type=result.question_type,
            question=result.question,
            answer=result.answer,
            depth_score=result.depth_score,
            is_ai_generated=False,
        )
        await self._repository.append_conversation_entry(session.id, entry)

        followup = await asyncio.to_thread(
            self._followup_generator.should_followup,
            answer=result.answer,
            topic=topic,
            conversation_log=None,
            current_followup_count=session.current_followup_count,
            depth_score=result.depth_score,
            seed=int(session.id.int & 0xFFFFFFFF),
        )

        if followup.need_followup:
            session.is_followup = True
            session.current_followup_is_ai = followup.is_ai_generated
            session.current_followup_count = session.current_followup_count + 1
            session.current_followup_question = followup.followup_question
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message=followup.followup_question, is_finished=False
            )

        # 进入下一题
        session.current_question_idx += 1
        session.is_followup = False
        session.current_followup_is_ai = False
        session.current_followup_count = 0
        session.current_followup_question = ""

        if session.current_question_idx >= self._total_questions:
            session.finish()
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message="访谈已结束，感谢您的参与！", is_finished=True
            )

        await self._repository.save(session)
        return InterviewResultDTO(
            assistant_message=self._current_question_text(session), is_finished=False
        )

    async def _process_followup_answer(
        self, *, session: Session, topic: dict[str, Any], answer: str
    ) -> InterviewResultDTO:
        followup_q = session.current_followup_question or "（追问）"
        result = self._answer_processor.process_followup_answer(
            answer=answer,
            topic=topic,
            followup_question=followup_q,
            is_ai_generated=bool(session.current_followup_is_ai),
        )

        entry = ConversationEntry(
            timestamp=result.timestamp,
            topic=result.topic,
            question_type=result.question_type,
            question=result.question,
            answer=result.answer,
            depth_score=result.depth_score,
            is_ai_generated=result.is_ai_generated,
        )
        await self._repository.append_conversation_entry(session.id, entry)

        followup = await asyncio.to_thread(
            self._followup_generator.should_followup,
            answer=result.answer,
            topic=topic,
            conversation_log=None,
            current_followup_count=session.current_followup_count,
            depth_score=result.depth_score,
            seed=int(session.id.int & 0xFFFFFFFF),
        )

        if followup.need_followup:
            session.is_followup = True
            session.current_followup_is_ai = followup.is_ai_generated
            session.current_followup_count = session.current_followup_count + 1
            session.current_followup_question = followup.followup_question
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message=followup.followup_question, is_finished=False
            )

        # 追问结束，进入下一题
        session.is_followup = False
        session.current_followup_is_ai = False
        session.current_followup_count = 0
        session.current_followup_question = ""
        session.current_question_idx += 1

        if session.current_question_idx >= self._total_questions:
            session.finish()
            await self._repository.save(session)
            return InterviewResultDTO(
                assistant_message="访谈已结束，感谢您的参与！", is_finished=True
            )

        await self._repository.save(session)
        return InterviewResultDTO(
            assistant_message=self._current_question_text(session), is_finished=False
        )
