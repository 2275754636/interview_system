#!/usr/bin/env python3
# coding: utf-8
"""
Session Manager - Core session lifecycle management
Delegates export and statistics to specialized modules
"""

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

import interview_system.common.logger as logger
from interview_system.common.config import WEB_CONFIG, ensure_dirs

# 尝试导入数据库模块（可选依赖）
try:
    from interview_system.data.database import get_database
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logger.warning("数据库模块未加载，会话数据仅保存在内存中")


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
    current_followup_is_ai: bool = False  # 当前追问是否为AI生成
    current_followup_count: int = 0  # 当前问题的追问次数
    current_followup_question: str = ""  # 当前追问的问题内容
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
            "conversation_log": self.conversation_log,
            "is_followup": self.is_followup,
            "current_followup_is_ai": self.current_followup_is_ai,
            "current_followup_count": self.current_followup_count,
            "current_followup_question": self.current_followup_question,
        }

    @classmethod
    def from_db_dict(cls, data: dict) -> 'InterviewSession':
        """从数据库字典创建会话对象"""
        return cls(
            session_id=data.get('session_id', ''),
            user_name=data.get('user_name', '访谈者'),
            start_time=data.get('start_time', ''),
            end_time=data.get('end_time', ''),
            is_finished=data.get('is_finished', False),
            current_question_idx=data.get('current_question_idx', 0),
            is_followup=data.get('is_followup', False),
            current_followup_is_ai=data.get('current_followup_is_ai', False),
            current_followup_count=data.get('current_followup_count', 0),
            current_followup_question=data.get('current_followup_question', ''),
            selected_topics=data.get('selected_topics', []),
            conversation_log=[]  # 日志需要单独加载
        )


class SessionManager:
    """Session manager - supports concurrent interviews"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Singleton pattern"""
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

        self._db = get_database() if DATABASE_AVAILABLE else None

        # Lazy import to avoid circular dependency
        from interview_system.services.session_exporter import SessionExporter
        from interview_system.services.session_statistics import SessionStatistics

        self._exporter = SessionExporter(self)
        self._statistics = SessionStatistics(self)

        ensure_dirs()
        db_status = "已启用" if self._db else "未启用"
        logger.info(f"会话管理器初始化完成 (数据库: {db_status})")
    
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

            # 同步保存到数据库
            if self._db:
                self._db.create_session(
                    session_id=session.session_id,
                    user_name=session.user_name,
                    selected_topics=session.selected_topics
                )

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
        # 先从内存中获取
        session = self._sessions.get(session_id)

        # 如果内存中没有，尝试从数据库加载
        if not session and self._db:
            db_session = self._db.get_session(session_id)
            if db_session:
                session = InterviewSession.from_db_dict(db_session)
                # 加载对话日志
                session.conversation_log = self._db.get_conversation_logs(session_id)
                # 缓存到内存
                self._sessions[session_id] = session

        return session
    
    def update_session(self, session: InterviewSession):
        """
        更新会话

        Args:
            session: 会话对象
        """
        with self._session_lock:
            self._sessions[session.session_id] = session

            # 同步更新到数据库
            if self._db:
                self._db.update_session(
                    session_id=session.session_id,
                    current_question_idx=session.current_question_idx,
                    selected_topics=session.selected_topics,
                    is_finished=session.is_finished,
                    end_time=session.end_time if session.end_time else None,
                    is_followup=session.is_followup,
                    current_followup_is_ai=session.current_followup_is_ai,
                    current_followup_count=session.current_followup_count,
                    current_followup_question=session.current_followup_question
                )

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

            # 同步更新到数据库
            if self._db:
                self._db.update_session(
                    session_id=session_id,
                    is_finished=True,
                    end_time=session.end_time
                )

            logger.log_session(session_id, "结束会话")
            return True
        return False

    def add_conversation_log(self, session_id: str, log_entry: Dict) -> bool:
        """
        添加对话日志

        Args:
            session_id: 会话ID
            log_entry: 日志条目

        Returns:
            是否成功添加
        """
        session = self.get_session(session_id)
        if not session:
            return False

        # 添加到内存
        session.conversation_log.append(log_entry)

        # 同步保存到数据库
        if self._db:
            self._db.add_conversation_log(session_id, log_entry)

        return True

    def rollback_session(self, session_id: str, *, target_log_count: int, session_state: dict) -> bool:
        """
        回滚会话到指定状态（用于撤回）

        Args:
            session_id: 会话ID
            target_log_count: 回滚后应保留的对话日志条数
            session_state: 需要恢复的会话状态字段快照

        Returns:
            是否回滚成功
        """
        with self._session_lock:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"回滚失败：会话 {session_id} 不存在")
                return False

            current_log_count = len(session.conversation_log)
            if target_log_count < 0 or target_log_count > current_log_count:
                logger.warning(
                    f"回滚失败：target_log_count={target_log_count} 不合法（当前={current_log_count}）"
                )
                return False

            delete_log_count = current_log_count - target_log_count

            # 数据库可用时必须原子回滚，失败则不应修改内存
            if self._db:
                is_finished = bool(session_state.get("is_finished", False))
                end_time = session_state.get("end_time") if is_finished else None
                session_update = {
                    "current_question_idx": session_state.get("current_question_idx", 0),
                    "is_finished": is_finished,
                    "end_time": end_time,
                    "is_followup": bool(session_state.get("is_followup", False)),
                    "current_followup_is_ai": bool(session_state.get("current_followup_is_ai", False)),
                    "current_followup_count": int(session_state.get("current_followup_count", 0)),
                    "current_followup_question": session_state.get("current_followup_question", "") or "",
                }

                ok = self._db.rollback_session_state(
                    session_id,
                    delete_log_count=delete_log_count,
                    session_update=session_update
                )
                if not ok:
                    logger.error(f"回滚失败：数据库回滚未成功 (session_id={session_id})")
                    return False

            # 回滚内存状态
            session.conversation_log = session.conversation_log[:target_log_count]
            session.current_question_idx = int(session_state.get("current_question_idx", session.current_question_idx))
            session.is_finished = bool(session_state.get("is_finished", session.is_finished))
            session.end_time = session_state.get("end_time", session.end_time) or ""
            if not session.is_finished:
                session.end_time = ""

            session.is_followup = bool(session_state.get("is_followup", session.is_followup))
            session.current_followup_is_ai = bool(session_state.get("current_followup_is_ai", session.current_followup_is_ai))
            session.current_followup_count = int(session_state.get("current_followup_count", session.current_followup_count))
            session.current_followup_question = session_state.get("current_followup_question", session.current_followup_question) or ""

            self._sessions[session.session_id] = session

            logger.log_session(session_id, "回滚会话", f"logs={current_log_count}->{target_log_count}")
            return True
    
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
        """获取所有会话（优先从数据库加载）"""
        if self._db:
            # 从数据库加载所有会话
            db_sessions = self._db.get_all_sessions(limit=1000)
            sessions = []
            for db_session in db_sessions:
                # 先尝试从内存获取
                session = self._sessions.get(db_session['session_id'])
                if not session:
                    # 从数据库数据创建会话对象（不加载完整日志，提高性能）
                    session = InterviewSession.from_db_dict(db_session)
                sessions.append(session)
            return sessions
        else:
            # 仅返回内存中的会话
            return list(self._sessions.values())
    
    def export_session(self, session_id: str, file_path: str = None) -> Optional[str]:
        """
        Export session to JSON file

        Returns:
            File path on success, None on failure
        """
        return self._exporter.export_session(session_id, file_path)

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
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

    def get_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """Get statistics - delegates to SessionStatistics"""
        return self._statistics.get_statistics(start_date, end_date)

    def get_daily_statistics(self, days: int = 7) -> List[Dict]:
        """Get daily statistics - delegates to SessionStatistics"""
        return self._statistics.get_daily_statistics(days)

    def get_session_count(self) -> int:
        """Get total session count - delegates to SessionStatistics"""
        return self._statistics.get_session_count()


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
