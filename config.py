#!/usr/bin/env python3
# coding: utf-8
"""
配置文件 - 大学生五育并举访谈智能体
包含 API 配置、系统参数等
"""

import os
from dataclasses import dataclass, field

# ----------------------------
# 路径配置
# ----------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, "logs")
EXPORT_DIR = os.path.join(BASE_DIR, "exports")


# ----------------------------
# 访谈系统配置
# ----------------------------
@dataclass
class InterviewConfig:
    """访谈系统配置"""
    total_questions: int = 6  # 每次访谈的题目数量
    min_answer_length: int = 30  # 触发追问的最小回答长度
    max_followup_length: int = 25  # AI追问最大长度
    max_depth_score: int = 3  # 回答深度最高分
    
    # 深度评分关键词
    depth_keywords: list = field(default_factory=lambda: [
        "例子", "情景", "经历", "具体", "我学到", "我的感受", 
        "影响", "计划", "应用", "反思", "目标", "回忆", 
        "思考", "帮助", "自立", "支持", "收获"
    ])
    
    # 通用关键词（用于提取回答关键词）
    common_keywords: list = field(default_factory=lambda: [
        "时间", "方法", "计划", "目标", "团队", 
        "互动", "冲突", "经验", "学习", "情绪"
    ])


# ----------------------------
# Web 服务配置
# ----------------------------
@dataclass
class WebConfig:
    """Web服务配置"""
    host: str = "0.0.0.0"
    port: int = 7860
    share: bool = True  # 是否生成公网链接
    title: str = "大学生五育并举访谈智能体"
    max_sessions: int = 100  # 最大同时会话数
    session_timeout: int = 3600  # 会话超时时间（秒）


# ----------------------------
# 日志配置
# ----------------------------
@dataclass
class LogConfig:
    """日志配置"""
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    log_to_file: bool = True
    log_to_console: bool = True
    log_format: str = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


# ----------------------------
# 默认配置实例
# ----------------------------
INTERVIEW_CONFIG = InterviewConfig()
WEB_CONFIG = WebConfig()
LOG_CONFIG = LogConfig()


# ----------------------------
# 确保目录存在
# ----------------------------
def ensure_dirs():
    """确保必要的目录存在"""
    for dir_path in [LOG_DIR, EXPORT_DIR]:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
