"""后台监管 API Schema。"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class AdminOverviewSummary(BaseModel):
    total_sessions: int = Field(..., ge=0)
    total_messages: int = Field(..., ge=0)
    active_users: int = Field(..., ge=0)
    avg_depth_score: float = Field(..., ge=0)


class AdminTimeSeriesPoint(BaseModel):
    bucket: str
    sessions: int = Field(..., ge=0)
    messages: int = Field(..., ge=0)
    unique_users: int = Field(..., ge=0)
    avg_depth_score: float = Field(..., ge=0)


class AdminUserActivityRow(BaseModel):
    user_name: str
    sessions: int = Field(..., ge=0)
    messages: int = Field(..., ge=0)


class AdminTopicRow(BaseModel):
    topic: str
    messages: int = Field(..., ge=0)
    avg_depth_score: float = Field(..., ge=0)


class AdminOverviewResponse(BaseModel):
    summary: AdminOverviewSummary
    time_series: list[AdminTimeSeriesPoint]
    top_users: list[AdminUserActivityRow]
    top_topics: list[AdminTopicRow]


class AdminListResponse(BaseModel):
    total: int = Field(..., ge=0)
    items: list[dict]


class AdminSearchResponse(BaseModel):
    total: int = Field(..., ge=0)
    items: list[dict]


class AdminExportFormat(BaseModel):
    format: Literal["csv", "json", "xlsx"]


class AdminExportQuery(BaseModel):
    scope: Literal["sessions", "conversations"] = "conversations"
    format: Literal["csv", "json", "xlsx"] = "csv"
    start: datetime | None = None
    end: datetime | None = None
    user_name: str | None = None
    topic: str | None = None
    keyword: str | None = None
    min_depth: int | None = Field(default=None, ge=0)
    max_depth: int | None = Field(default=None, ge=0)
    limit: int = Field(default=5000, ge=1, le=20000)
    offset: int = Field(default=0, ge=0)

