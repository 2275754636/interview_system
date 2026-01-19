"""后台监管路由（导出/指标/研究查询）。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response

from interview_system.api.deps import get_admin_service, require_admin_token
from interview_system.api.schemas.admin import (
    AdminListResponse,
    AdminOverviewResponse,
    AdminSearchResponse,
)
from interview_system.api.utils.xlsx import build_xlsx
from interview_system.application.services.admin_service import AdminService

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin_token)],
)


@router.get("/overview", response_model=AdminOverviewResponse)
async def overview(
    service: AdminService = Depends(get_admin_service),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    bucket: Literal["day", "hour"] = Query(default="day"),
    top_n: int = Query(default=10, ge=1, le=50),
):
    return await service.overview(start=start, end=end, bucket=bucket, top_n=top_n)


@router.get("/sessions", response_model=AdminListResponse)
async def list_sessions(
    service: AdminService = Depends(get_admin_service),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    user_name: str | None = Query(default=None),
    is_finished: bool | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await service.list_sessions(
        start=start,
        end=end,
        user_name=user_name,
        is_finished=is_finished,
        limit=limit,
        offset=offset,
    )


@router.get("/search", response_model=AdminSearchResponse)
async def search(
    service: AdminService = Depends(get_admin_service),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    user_name: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    min_depth: int | None = Query(default=None, ge=0),
    max_depth: int | None = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    return await service.search_conversations(
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


@router.get("/export")
async def export(
    service: AdminService = Depends(get_admin_service),
    scope: Literal["sessions", "conversations"] = Query(default="conversations"),
    format: Literal["csv", "json", "xlsx"] = Query(default="csv"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    user_name: str | None = Query(default=None),
    topic: str | None = Query(default=None),
    keyword: str | None = Query(default=None),
    min_depth: int | None = Query(default=None, ge=0),
    max_depth: int | None = Query(default=None, ge=0),
    limit: int = Query(default=5000, ge=1, le=20000),
    offset: int = Query(default=0, ge=0),
):
    base_name, items = await service.export_rows(
        scope=scope,
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

    file_stem = f"{base_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

    if format == "json":
        body = service.to_json(items)
        return Response(
            content=body,
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="{file_stem}.json"'
            },
        )

    if format == "xlsx":
        if not items:
            rows: list[list[str]] = [["empty"]]
        else:
            headers = list(items[0].keys())
            rows = [headers]
            for item in items:
                rows.append([str(item.get(h, "")) for h in headers])

        body = build_xlsx(rows=rows, sheet_name=base_name)
        return Response(
            content=body,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f'attachment; filename="{file_stem}.xlsx"'
            },
        )

    body = service.to_csv(items)
    return Response(
        content=body,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{file_stem}.csv"'},
    )

