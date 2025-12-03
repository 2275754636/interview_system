#!/usr/bin/env python3
# coding: utf-8
"""
日志模块 - 大学生五育并举访谈智能体
提供统一的日志输出功能
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from config import LOG_CONFIG, LOG_DIR, ensure_dirs


class InterviewLogger:
    """访谈系统日志管理器"""
    
    _loggers = {}  # 缓存已创建的 logger
    
    @classmethod
    def get_logger(cls, name: str = "interview") -> logging.Logger:
        """
        获取日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            配置好的 Logger 实例
        """
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 确保日志目录存在
        ensure_dirs()
        
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, LOG_CONFIG.level))
        logger.handlers = []  # 清除已有的 handlers
        
        # 创建格式化器
        formatter = logging.Formatter(
            LOG_CONFIG.log_format,
            datefmt=LOG_CONFIG.date_format
        )
        
        # 控制台输出
        if LOG_CONFIG.log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(getattr(logging, LOG_CONFIG.level))
            logger.addHandler(console_handler)
        
        # 文件输出
        if LOG_CONFIG.log_to_file:
            log_file = os.path.join(
                LOG_DIR, 
                f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            )
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=LOG_CONFIG.max_file_size,
                backupCount=LOG_CONFIG.backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(getattr(logging, LOG_CONFIG.level))
            logger.addHandler(file_handler)
        
        cls._loggers[name] = logger
        return logger


# ----------------------------
# 便捷日志函数
# ----------------------------
_default_logger: Optional[logging.Logger] = None


def _get_default_logger() -> logging.Logger:
    """获取默认日志记录器"""
    global _default_logger
    if _default_logger is None:
        _default_logger = InterviewLogger.get_logger("interview")
    return _default_logger


def debug(msg: str, *args, **kwargs):
    """记录调试日志"""
    _get_default_logger().debug(msg, *args, **kwargs)


def info(msg: str, *args, **kwargs):
    """记录信息日志"""
    _get_default_logger().info(msg, *args, **kwargs)


def warning(msg: str, *args, **kwargs):
    """记录警告日志"""
    _get_default_logger().warning(msg, *args, **kwargs)


def error(msg: str, *args, **kwargs):
    """记录错误日志"""
    _get_default_logger().error(msg, *args, **kwargs)


def critical(msg: str, *args, **kwargs):
    """记录严重错误日志"""
    _get_default_logger().critical(msg, *args, **kwargs)


def exception(msg: str, *args, **kwargs):
    """记录异常日志（包含堆栈信息）"""
    _get_default_logger().exception(msg, *args, **kwargs)


# ----------------------------
# 特定场景的日志记录
# ----------------------------
def log_api_call(api_name: str, success: bool, duration: float, error_msg: str = None):
    """记录API调用日志"""
    logger = InterviewLogger.get_logger("api")
    if success:
        logger.info(f"API调用成功 - {api_name} - 耗时: {duration:.2f}s")
    else:
        logger.error(f"API调用失败 - {api_name} - 耗时: {duration:.2f}s - 错误: {error_msg}")


def log_session(session_id: str, action: str, details: str = None):
    """记录会话日志"""
    logger = InterviewLogger.get_logger("session")
    msg = f"会话 [{session_id}] - {action}"
    if details:
        msg += f" - {details}"
    logger.info(msg)


def log_interview(session_id: str, event: str, data: dict = None):
    """记录访谈事件日志"""
    logger = InterviewLogger.get_logger("interview")
    msg = f"访谈 [{session_id}] - {event}"
    if data:
        msg += f" - {data}"
    logger.info(msg)
