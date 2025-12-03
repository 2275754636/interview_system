#!/usr/bin/env python3
# coding: utf-8
"""
大学生五育并举访谈智能体

模块结构:
- config.py: 配置文件（API设置、系统参数）
- questions.py: 题目配置（15个访谈话题）
- logger.py: 日志模块（统一日志输出）
- api_client.py: API客户端（百度千帆，含重试机制）
- session_manager.py: 会话管理（支持多人同时访谈）
- interview_engine.py: 访谈核心引擎（追问逻辑、评分）
- web_server.py: Web服务（Gradio界面）
- main.py: 主入口
"""

from .config import (
    BAIDU_API_CONFIG,
    INTERVIEW_CONFIG,
    WEB_CONFIG,
    LOG_CONFIG,
    ensure_dirs
)

from .questions import TOPICS, SCENES, EDU_TYPES

from .api_client import (
    initialize_api,
    is_api_available,
    generate_followup
)

from .session_manager import (
    create_session,
    get_session,
    export_session,
    get_session_manager
)

from .interview_engine import (
    create_interview,
    get_interview_engine,
    InterviewEngine
)

from .web_server import (
    start_web_server,
    check_gradio_available
)

__version__ = "2.0.0"
__author__ = "Interview System"
