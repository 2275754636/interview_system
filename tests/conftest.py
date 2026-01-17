"""Pytest 共享 fixture 配置。"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from interview_system.api.main import create_app
from interview_system.config.settings import Settings


@pytest.fixture(scope="function")
def test_settings() -> Settings:
    """测试环境配置。"""
    return Settings(
        database_url="sqlite+aiosqlite:///:memory:",
        log_level="INFO",
        allowed_origins=[],
    )


@pytest.fixture(scope="function")
def app(test_settings: Settings):
    """FastAPI 应用实例。"""
    return create_app(test_settings)


@pytest.fixture(scope="function")
def client(app):
    """同步测试客户端。"""
    with TestClient(app) as c:
        yield c
