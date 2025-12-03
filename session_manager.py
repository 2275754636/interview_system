#!/usr/bin/env python3
# coding: utf-8
"""
会话管理模块 - 大学生五育并举访谈智能体
支持多人同时访谈的会话管理
"""

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import logger
from config import WEB_CONFIG, EXPORT_DIR, ensure_dirs


@dataclass
class InterviewSession:
    """访谈会话"""
    session_id: str
    user_name: str = "访谈者"
    start_time: str = ""
    end_time: str = ""
    is_finished: bool = False
    current_question_idx: int = 0
    is_followup: bool = False
    selected_topics: List[Dict] = field(default_factory=list)
    conversation_log: List[Dict] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "user_name": self.user_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "is_finished": self.is_finished,
            "current_question_idx": self.current_question_idx,
            "conversation_log": self.conversation_log
        }


class SessionManager:
    """会话管理器 - 支持多人同时访谈"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._sessions: Dict[str, InterviewSession] = {}
        self._session_lock = threading.Lock()
        self._max_sessions = WEB_CONFIG.max_sessions
        self._initialized = True
        
        ensure_dirs()
        logger.info("会话管理器初始化完成")
    
    def create_session(self, user_name: str = None) -> InterviewSession:
        """
        创建新会话
        
        Args:
            user_name: 用户名（可选）
            
        Returns:
            新创建的会话
        """
        with self._session_lock:
            # 检查会话数量限制
            if len(self._sessions) >= self._max_sessions:
                self._cleanup_expired_sessions()
                
                if len(self._sessions) >= self._max_sessions:
                    logger.warning("会话数量已达上限，清理最旧的会话")
                    self._remove_oldest_session()
            
            # 创建新会话
            session_id = str(uuid.uuid4())[:8]
            session = InterviewSession(
                session_id=session_id,
                user_name=user_name or f"访谈者_{session_id}"
            )
            
            self._sessions[session_id] = session
            logger.log_session(session_id, "创建会话", f"用户: {session.user_name}")
            
            return session
    
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """
        获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话对象，不存在返回 None
        """
        return self._sessions.get(session_id)
    
    def update_session(self, session: InterviewSession):
        """
        更新会话
        
        Args:
            session: 会话对象
        """
        with self._session_lock:
            self._sessions[session.session_id] = session
    
    def end_session(self, session_id: str) -> bool:
        """
        结束会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功结束
        """
        session = self.get_session(session_id)
        if session:
            session.is_finished = True
            session.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.log_session(session_id, "结束会话")
            return True
        return False
    
    def remove_session(self, session_id: str) -> bool:
        """
        移除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功移除
        """
        with self._session_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.log_session(session_id, "移除会话")
                return True
        return False
    
    def get_active_session_count(self) -> int:
        """获取活跃会话数量"""
        return sum(1 for s in self._sessions.values() if not s.is_finished)
    
    def get_all_sessions(self) -> List[InterviewSession]:
        """获取所有会话"""
        return list(self._sessions.values())
    
    def export_session(self, session_id: str, file_path: str = None) -> Optional[str]:
        """
        导出会话到JSON文件
        
        Args:
            session_id: 会话ID
            file_path: 导出路径（可选）
            
        Returns:
            导出的文件路径，失败返回 None
        """
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"导出失败：会话 {session_id} 不存在")
            return None
        
        # 生成统计信息
        summary = self._generate_summary(session)
        
        # 确定文件路径
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(
                EXPORT_DIR, 
                f"interview_{session.user_name}_{timestamp}.json"
            )
        
        # 导出到文件
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            logger.log_session(session_id, "导出会话", f"文件: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出会话失败: {e}")
            return None
    
    def _generate_summary(self, session: InterviewSession) -> dict:
        """生成会话摘要"""
        # 统计场景分布
        scene_stats = {}
        edu_stats = {}
        followup_stats = {"预设追问": 0, "AI智能追问": 0}
        
        for log in session.conversation_log:
            topic = log.get("topic", "")
            if "-" in topic:
                scene, edu = topic.split("-")
                scene_stats[scene] = scene_stats.get(scene, 0) + 1
                edu_stats[edu] = edu_stats.get(edu, 0) + 1
            
            q_type = log.get("question_type", "")
            if "追问" in q_type:
                if log.get("is_ai_generated"):
                    followup_stats["AI智能追问"] += 1
                else:
                    followup_stats["预设追问"] += 1
        
        return {
            "session_id": session.session_id,
            "user_name": session.user_name,
            "start_time": session.start_time,
            "end_time": session.end_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "statistics": {
                "total_logs": len(session.conversation_log),
                "scene_distribution": scene_stats,
                "edu_distribution": edu_stats,
                "followup_distribution": followup_stats
            },
            "conversation_log": session.conversation_log
        }
    
    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        from config import WEB_CONFIG
        timeout = WEB_CONFIG.session_timeout
        now = datetime.now()
        
        expired = []
        for sid, session in self._sessions.items():
            try:
                start = datetime.strptime(session.start_time, "%Y-%m-%d %H:%M:%S")
                if (now - start).total_seconds() > timeout:
                    expired.append(sid)
            except:
                pass
        
        for sid in expired:
            del self._sessions[sid]
            logger.log_session(sid, "清理过期会话")
    
    def _remove_oldest_session(self):
        """移除最旧的会话"""
        if not self._sessions:
            return
        
        oldest_sid = min(
            self._sessions.keys(),
            key=lambda x: self._sessions[x].start_time
        )
        del self._sessions[oldest_sid]
        logger.log_session(oldest_sid, "移除最旧会话")


# ----------------------------
# 便捷函数
# ----------------------------
def get_session_manager() -> SessionManager:
    """获取会话管理器单例"""
    return SessionManager()


def create_session(user_name: str = None) -> InterviewSession:
    """创建新会话"""
    return get_session_manager().create_session(user_name)


def get_session(session_id: str) -> Optional[InterviewSession]:
    """获取会话"""
    return get_session_manager().get_session(session_id)


def export_session(session_id: str, file_path: str = None) -> Optional[str]:
    """导出会话"""
    return get_session_manager().export_session(session_id, file_path)
