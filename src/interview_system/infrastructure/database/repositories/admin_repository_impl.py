"""AdminRepository 的 SQLAlchemy async 实现（审计/研究查询）。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select

from interview_system.domain.repositories.admin_repository import (
    AdminConversationRow,
    AdminRepository,
    AdminSessionRow,
    AdminTimeSeriesPoint,
    AdminTopicRow,
    AdminUserActivityRow,
)
from interview_system.infrastructure.database.connection import AsyncDatabase
from interview_system.infrastructure.database.models import (
    ConversationLogModel,
    SessionModel,
)

_TS_FORMAT = "%Y-%m-%d %H:%M:%S"


def _to_utc_text(dt: datetime) -> str:
    normalized = dt
    if dt.tzinfo is None:
        normalized = dt.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).strftime(_TS_FORMAT)


def _bucket_expr(column, bucket: str):  # noqa: ANN001
    if bucket == "hour":
        return func.substr(column, 1, 13)
    return func.substr(column, 1, 10)


class AdminRepositoryImpl(AdminRepository):
    def __init__(self, db: AsyncDatabase) -> None:
        self._db = db

    async def list_sessions(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        user_name: str | None,
        is_finished: bool | None,
        limit: int,
        offset: int,
    ) -> tuple[int, list[AdminSessionRow]]:
        where = []
        if start is not None:
            where.append(SessionModel.start_time >= _to_utc_text(start))
        if end is not None:
            where.append(SessionModel.start_time < _to_utc_text(end))
        if user_name:
            where.append(SessionModel.user_name == user_name)
        if is_finished is not None:
            where.append(SessionModel.is_finished == (1 if is_finished else 0))

        where_clause = and_(*where) if where else None

        async with self._db.session() as session:
            total_stmt = select(func.count()).select_from(SessionModel)
            if where_clause is not None:
                total_stmt = total_stmt.where(where_clause)
            total = int((await session.execute(total_stmt)).scalar_one())

            stmt = select(SessionModel).order_by(SessionModel.start_time.desc())
            if where_clause is not None:
                stmt = stmt.where(where_clause)
            stmt = stmt.limit(int(limit)).offset(int(offset))
            models = (await session.execute(stmt)).scalars().all()

        rows: list[AdminSessionRow] = []
        for m in models:
            rows.append(
                AdminSessionRow(
                    session_id=m.session_id,
                    user_name=m.user_name,
                    start_time=m.start_time,
                    end_time=m.end_time,
                    is_finished=bool(m.is_finished),
                    current_question_idx=int(m.current_question_idx or 0),
                    selected_topics_json=m.selected_topics,
                    created_at=m.created_at,
                    updated_at=m.updated_at,
                    is_followup=bool(m.is_followup),
                    current_followup_is_ai=bool(m.current_followup_is_ai),
                    current_followup_count=int(m.current_followup_count or 0),
                    current_followup_question=m.current_followup_question or "",
                )
            )

        return total, rows

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
    ) -> tuple[int, list[AdminConversationRow]]:
        where = []
        if start is not None:
            where.append(ConversationLogModel.timestamp >= _to_utc_text(start))
        if end is not None:
            where.append(ConversationLogModel.timestamp < _to_utc_text(end))
        if user_name:
            where.append(SessionModel.user_name == user_name)
        if topic:
            where.append(ConversationLogModel.topic == topic)
        if min_depth is not None:
            where.append(ConversationLogModel.depth_score >= int(min_depth))
        if max_depth is not None:
            where.append(ConversationLogModel.depth_score <= int(max_depth))
        if keyword:
            kw = f"%{keyword.strip().lower()}%"
            where.append(
                or_(
                    func.lower(ConversationLogModel.question).like(kw),
                    func.lower(ConversationLogModel.answer).like(kw),
                )
            )

        where_clause = and_(*where) if where else None

        async with self._db.session() as session:
            base = (
                select(ConversationLogModel, SessionModel.user_name)
                .join(SessionModel, SessionModel.session_id == ConversationLogModel.session_id)
            )
            total_stmt = select(func.count()).select_from(
                base.subquery()
            )
            if where_clause is not None:
                base = base.where(where_clause)
                total_stmt = select(func.count()).select_from(base.subquery())
            total = int((await session.execute(total_stmt)).scalar_one())

            stmt = base.order_by(ConversationLogModel.id.desc()).limit(int(limit)).offset(
                int(offset)
            )
            result = await session.execute(stmt)
            items = result.all()

        rows: list[AdminConversationRow] = []
        for log, uname in items:
            rows.append(
                AdminConversationRow(
                    id=int(log.id),
                    session_id=log.session_id,
                    user_name=str(uname or ""),
                    timestamp=log.timestamp,
                    topic=log.topic or "",
                    question_type=log.question_type or "",
                    question=log.question or "",
                    answer=log.answer or "",
                    depth_score=int(log.depth_score or 0),
                    is_ai_generated=bool(log.is_ai_generated),
                )
            )
        return total, rows

    async def get_time_series(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        bucket: str,
    ) -> list[AdminTimeSeriesPoint]:
        bucket = "hour" if bucket == "hour" else "day"

        session_where = []
        log_where = []
        if start is not None:
            session_where.append(SessionModel.start_time >= _to_utc_text(start))
            log_where.append(ConversationLogModel.timestamp >= _to_utc_text(start))
        if end is not None:
            session_where.append(SessionModel.start_time < _to_utc_text(end))
            log_where.append(ConversationLogModel.timestamp < _to_utc_text(end))

        async with self._db.session() as session:
            sess_bucket = _bucket_expr(SessionModel.start_time, bucket).label("bucket")
            sess_stmt = (
                select(
                    sess_bucket,
                    func.count().label("sessions"),
                    func.count(func.distinct(SessionModel.user_name)).label("users"),
                )
                .select_from(SessionModel)
                .group_by(sess_bucket)
                .order_by(sess_bucket.asc())
            )
            if session_where:
                sess_stmt = sess_stmt.where(and_(*session_where))
            sess_rows = (await session.execute(sess_stmt)).all()

            log_bucket = _bucket_expr(ConversationLogModel.timestamp, bucket).label("bucket")
            log_stmt = (
                select(
                    log_bucket,
                    func.count().label("messages"),
                    func.avg(ConversationLogModel.depth_score).label("avg_depth"),
                )
                .select_from(ConversationLogModel)
                .group_by(log_bucket)
                .order_by(log_bucket.asc())
            )
            if log_where:
                log_stmt = log_stmt.where(and_(*log_where))
            log_rows = (await session.execute(log_stmt)).all()

        sessions_by_bucket: dict[str, tuple[int, int]] = {
            str(b): (int(s or 0), int(u or 0)) for b, s, u in sess_rows
        }
        logs_by_bucket: dict[str, tuple[int, float]] = {
            str(b): (int(m or 0), float(d or 0.0)) for b, m, d in log_rows
        }

        all_buckets = sorted(set(sessions_by_bucket.keys()) | set(logs_by_bucket.keys()))
        out: list[AdminTimeSeriesPoint] = []
        for b in all_buckets:
            s, u = sessions_by_bucket.get(b, (0, 0))
            m, d = logs_by_bucket.get(b, (0, 0.0))
            out.append(
                AdminTimeSeriesPoint(
                    bucket=b,
                    sessions=int(s),
                    messages=int(m),
                    unique_users=int(u),
                    avg_depth_score=float(round(d, 4)),
                )
            )
        return out

    async def get_user_activity(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[AdminUserActivityRow]:
        session_where = []
        log_where = []
        if start is not None:
            session_where.append(SessionModel.start_time >= _to_utc_text(start))
            log_where.append(ConversationLogModel.timestamp >= _to_utc_text(start))
        if end is not None:
            session_where.append(SessionModel.start_time < _to_utc_text(end))
            log_where.append(ConversationLogModel.timestamp < _to_utc_text(end))

        async with self._db.session() as session:
            join_on = [ConversationLogModel.session_id == SessionModel.session_id]
            if log_where:
                join_on.extend(log_where)
            stmt = (
                select(
                    SessionModel.user_name.label("user_name"),
                    func.count(func.distinct(SessionModel.session_id)).label("sessions"),
                    func.count(ConversationLogModel.id).label("messages"),
                )
                .select_from(SessionModel)
                .outerjoin(
                    ConversationLogModel,
                    and_(*join_on),
                )
                .group_by(SessionModel.user_name)
                .order_by(func.count(ConversationLogModel.id).desc())
                .limit(int(limit))
            )
            if session_where:
                stmt = stmt.where(and_(*session_where))
            rows = (await session.execute(stmt)).all()

        return [
            AdminUserActivityRow(
                user_name=str(r.user_name or ""),
                sessions=int(r.sessions or 0),
                messages=int(r.messages or 0),
            )
            for r in rows
        ]

    async def get_top_topics(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        limit: int,
    ) -> list[AdminTopicRow]:
        where = []
        if start is not None:
            where.append(ConversationLogModel.timestamp >= _to_utc_text(start))
        if end is not None:
            where.append(ConversationLogModel.timestamp < _to_utc_text(end))

        async with self._db.session() as session:
            stmt = (
                select(
                    ConversationLogModel.topic.label("topic"),
                    func.count().label("messages"),
                    func.avg(ConversationLogModel.depth_score).label("avg_depth"),
                )
                .select_from(ConversationLogModel)
                .group_by(ConversationLogModel.topic)
                .order_by(func.count().desc())
                .limit(int(limit))
            )
            if where:
                stmt = stmt.where(and_(*where))
            rows = (await session.execute(stmt)).all()

        return [
            AdminTopicRow(
                topic=str(r.topic or ""),
                messages=int(r.messages or 0),
                avg_depth_score=float(round(float(r.avg_depth or 0.0), 4)),
            )
            for r in rows
        ]
