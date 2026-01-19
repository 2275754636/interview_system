"""后台监管应用服务：导出、指标聚合、研究查询。"""

from __future__ import annotations

import csv
import io
import json
from dataclasses import asdict
from datetime import datetime
from typing import Any, Literal

from interview_system.domain.repositories.admin_repository import (
    AdminConversationRow,
    AdminRepository,
    AdminSessionRow,
)


def _safe_json_loads(raw: str | None) -> Any:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return raw


class AdminService:
    def __init__(self, repository: AdminRepository) -> None:
        self._repo = repository

    async def overview(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        bucket: Literal["day", "hour"] = "day",
        top_n: int = 10,
    ) -> dict[str, Any]:
        ts = await self._repo.get_time_series(start=start, end=end, bucket=bucket)
        users = await self._repo.get_user_activity(start=start, end=end, limit=top_n)
        topics = await self._repo.get_top_topics(start=start, end=end, limit=top_n)

        total_sessions = sum(p.sessions for p in ts)
        total_messages = sum(p.messages for p in ts)
        unique_users = len({u.user_name for u in users if u.user_name})
        avg_depth = (
            round(
                (
                    sum(p.avg_depth_score * p.messages for p in ts)
                    / max(total_messages, 1)
                ),
                4,
            )
            if ts
            else 0.0
        )

        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "active_users": unique_users,
                "avg_depth_score": avg_depth,
            },
            "time_series": [asdict(p) for p in ts],
            "top_users": [asdict(u) for u in users],
            "top_topics": [asdict(t) for t in topics],
        }

    async def list_sessions(
        self,
        *,
        start: datetime | None,
        end: datetime | None,
        user_name: str | None,
        is_finished: bool | None,
        limit: int,
        offset: int,
    ) -> dict[str, Any]:
        total, rows = await self._repo.list_sessions(
            start=start,
            end=end,
            user_name=user_name,
            is_finished=is_finished,
            limit=limit,
            offset=offset,
        )
        items: list[dict[str, Any]] = []
        for r in rows:
            items.append(
                {
                    **asdict(r),
                    "selected_topics": _safe_json_loads(r.selected_topics_json),
                }
            )
        return {"total": total, "items": items}

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
    ) -> dict[str, Any]:
        total, rows = await self._repo.search_conversations(
            start=start,
            end=end,
            user_name=user_name,
            topic=topic,
            keyword=keyword,
            min_depth=min_depth,
            max_depth=max_depth,
            limit=limit,
            offset=offset,
        )
        return {"total": total, "items": [asdict(r) for r in rows]}

    async def export_rows(
        self,
        *,
        scope: Literal["sessions", "conversations"],
        start: datetime | None,
        end: datetime | None,
        user_name: str | None,
        keyword: str | None,
        topic: str | None,
        min_depth: int | None,
        max_depth: int | None,
        limit: int,
        offset: int,
    ) -> tuple[str, list[dict[str, Any]]]:
        if scope == "sessions":
            payload = await self.list_sessions(
                start=start,
                end=end,
                user_name=user_name,
                is_finished=None,
                limit=limit,
                offset=offset,
            )
            return "sessions", list(payload["items"])

        payload = await self.search_conversations(
            start=start,
            end=end,
            user_name=user_name,
            topic=topic,
            keyword=keyword,
            min_depth=min_depth,
            max_depth=max_depth,
            limit=limit,
            offset=offset,
        )
        return "conversations", list(payload["items"])

    @staticmethod
    def to_csv(items: list[dict[str, Any]]) -> bytes:
        if not items:
            return b""

        headers = list(items[0].keys())
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in item.items()})
        return buf.getvalue().encode("utf-8-sig")

    @staticmethod
    def to_json(items: list[dict[str, Any]]) -> bytes:
        return json.dumps(items, ensure_ascii=False, indent=2).encode("utf-8")

