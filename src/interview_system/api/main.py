"""FastAPI 应用工厂。"""

from __future__ import annotations

import json
import logging
import os
import re
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interview_system.api.exceptions import register_exception_handlers
from interview_system.api.routes import health, interview, session
from interview_system.config import settings as _settings
from interview_system.config.logging import configure_logging
from interview_system.config.settings import Settings
from interview_system.infrastructure.cache.memory_cache import SessionCache
from interview_system.infrastructure.database.connection import AsyncDatabase

logger = logging.getLogger(__name__)


def _parse_cors_origins() -> list[str]:
    """从环境变量解析 CORS origin，fallback 为本地开发地址。"""
    env_origins = os.getenv("CORS_ORIGINS", "")
    return [o.strip() for o in env_origins.split(",") if o.strip()] or [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


def _parse_cors_allowed_host_suffixes() -> list[str]:
    """从环境变量解析公网 host 后缀白名单，用于构造 allow_origin_regex。"""
    raw = os.getenv("CORS_ALLOWED_HOST_SUFFIXES", "").strip()
    if not raw:
        return []
    suffixes: list[str] = []
    for part in raw.split(","):
        suffix = part.strip()
        if not suffix:
            continue
        suffixes.append(suffix)
    return suffixes


def _build_cors_allow_origin_regex() -> str | None:
    """构造 CORS allow_origin_regex（默认关闭，需通过环境变量显式开启）。"""
    suffixes = _parse_cors_allowed_host_suffixes()
    if not suffixes:
        return None

    escaped_suffixes: list[str] = []
    for suffix in suffixes:
        normalized = suffix.lstrip(".")
        if not normalized:
            continue
        escaped_suffixes.append(re.escape(normalized))

    if not escaped_suffixes:
        return None

    joined = "|".join(escaped_suffixes)
    return rf"^https://[a-z0-9-]+\.({joined})$"


def _unique_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        if v in seen:
            continue
        seen.add(v)
        out.append(v)
    return out


def _read_public_url_state_file(state_path: Path) -> dict[str, object]:
    """读取公网 URL 状态文件，解析失败会记录日志并返回默认状态。"""
    try:
        raw = state_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"url": None, "is_public": False}
    except Exception as e:
        logger.warning("读取公网 URL 状态失败: %s", e)
        return {"url": None, "is_public": False}

    try:
        data = json.loads(raw)
    except Exception as e:
        logger.warning("解析公网 URL 状态 JSON 失败: %s", e)
        return {"url": None, "is_public": False}

    if not isinstance(data, dict):
        logger.warning("公网 URL 状态格式非法: 期望 object")
        return {"url": None, "is_public": False}

    url = data.get("url")
    is_public = data.get("is_public")
    if is_public is not True or not isinstance(url, str) or not url:
        return {"url": None, "is_public": False}

    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return {"url": None, "is_public": False}

    return {"url": url, "is_public": True}


def get_public_url_state() -> dict[str, object]:
    """返回启动器写入的前端公网 URL 状态。"""
    state_path = os.getenv("PUBLIC_URL_STATE_PATH", "").strip()
    if not state_path:
        return {"url": None, "is_public": False}
    return _read_public_url_state_file(Path(state_path))


def create_app(settings: Settings) -> FastAPI:
    """创建 FastAPI app（允许测试时传入不同 Settings）。"""
    configure_logging(log_level=settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[misc]
        app.state.settings = settings
        app.state.session_cache = SessionCache()
        app.state.db = AsyncDatabase(settings.database_url)
        await app.state.db.init()
        yield
        await app.state.db.dispose()

    app = FastAPI(
        title="Interview System API",
        version="2.0.0",
        description="REST API for AI-powered interview platform",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    allow_origins = _unique_keep_order(_parse_cors_origins() + list(settings.allowed_origins))
    allow_origin_regex = _build_cors_allow_origin_regex()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_origin_regex=allow_origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(session.router, prefix="/api")
    app.include_router(interview.router, prefix="/api")
    app.include_router(health.router)

    @app.get("/api/public-url")
    async def public_url():
        """返回前端公网 URL 状态（由启动器写入，后端读取）。"""
        return get_public_url_state()

    @app.get("/")
    async def root():
        """返回 API 根信息。"""
        return {
            "service": "Interview System API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health",
        }

    return app


app = create_app(_settings)
