"""FastAPI 应用工厂。"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from interview_system.api.exceptions import register_exception_handlers
from interview_system.api.routes import health, interview, session
from interview_system.config import settings as _settings
from interview_system.config.logging import configure_logging
from interview_system.config.settings import Settings
from interview_system.infrastructure.cache.memory_cache import SessionCache
from interview_system.infrastructure.database.connection import AsyncDatabase


def _parse_cors_origins() -> list[str]:
    """从环境变量解析 CORS origin，fallback 为本地开发地址。"""
    env_origins = os.getenv("CORS_ORIGINS", "")
    return [o.strip() for o in env_origins.split(",") if o.strip()] or [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_cors_origins() + list(settings.allowed_origins),
        allow_origin_regex=r"https://.*\.(trycloudflare\.com|ngrok-free\.app|ngrok\.io)",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(session.router, prefix="/api")
    app.include_router(interview.router, prefix="/api")
    app.include_router(health.router)

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
