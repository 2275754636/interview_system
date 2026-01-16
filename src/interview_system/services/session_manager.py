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
    """Interview session state"""
    session_id: str
    user_name: str = "访谈者"
    start_time: str = ""
    end_time: str = ""
    is_finished: bool = False
    current_question_idx: int = 0
    is_followup: bool = False
    current_followup_is_ai: bool = False
    current_followup_count: int = 0
    current_followup_question: str = ""
    selected_topics: List[Dict] = field(default_factory=list)
    conversation_log: List[Dict] = field(default_factory=list)
    undo_stack: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.start_time:
            self.start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def to_dict(self) -> dict:
        """Convert to dict"""
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
        """Create from database dict"""
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
            conversation_log=[]
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

        # Initialize repositories
        if self._db:
            self.session_repo = self._db.sessions
            self.log_repo = self._db.logs
            self.stats_repo = self._db.statistics
        else:
            self.session_repo = None
            self.log_repo = None
            self.stats_repo = None

        from interview_system.services.session_statistics import SessionStatistics
        from interview_system.services.state_rollback import StateRollbackManager

        self._statistics = SessionStatistics(self)
        self._rollback_manager = StateRollbackManager(self._db)

        ensure_dirs()
        db_status = "已启用" if self._db else "未启用"
        logger.info(f"会话管理器初始化完成 (数据库: {db_status})")
    
    def create_session(self, user_name: str = None) -> InterviewSession:
        """Create new session"""
        with self._session_lock:
            if len(self._sessions) >= self._max_sessions:
                self._cleanup_expired_sessions()
                if len(self._sessions) >= self._max_sessions:
                    logger.warning("会话数量已达上限，清理最旧的会话")
                    self._remove_oldest_session()

            session_id = str(uuid.uuid4())[:8]
            session = InterviewSession(
                session_id=session_id,
                user_name=user_name or f"访谈者_{session_id}"
            )
            self._sessions[session_id] = session

            if self.session_repo:
                self.session_repo.create(
                    session.session_id,
                    session.user_name,
                    session.selected_topics
                )

            logger.log_session(session_id, "创建会话", f"用户: {session.user_name}")
            return session
    
    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        """Get session by ID"""
        session = self._sessions.get(session_id)

        if not session and self.session_repo:
            db_session = self.session_repo.get(session_id)
            if db_session:
                session = InterviewSession.from_db_dict(db_session)
                session.conversation_log = self.log_repo.get_by_session(session_id)
                self._sessions[session_id] = session

        return session
    
    def update_session(self, session: InterviewSession):
        """Update session"""
        with self._session_lock:
            self._sessions[session.session_id] = session

            if self.session_repo:
                self.session_repo.update(
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
        """End session"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.is_finished = True
        session.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if self.session_repo:
            self.session_repo.update(
                session_id=session_id,
                is_finished=True,
                end_time=session.end_time
            )

        logger.log_session(session_id, "结束会话")
        return True

    def add_conversation_log(self, session_id: str, log_entry: Dict) -> bool:
        """Add conversation log"""
        session = self.get_session(session_id)
        if not session:
            return False

        session.conversation_log.append(log_entry)

        if self.log_repo:
            self.log_repo.add(session_id, log_entry)

        return True

    def rollback_session(self, session_id: str, *, target_log_count: int, session_state: dict) -> bool:
        """Rollback session to specified state"""
        with self._session_lock:
            session = self.get_session(session_id)
            if not session:
                logger.warning(f"回滚失败：会话 {session_id} 不存在")
                return False

            success = self._rollback_manager.rollback(
                session,
                target_log_count=target_log_count,
                session_state=session_state
            )

            if success:
                self._sessions[session.session_id] = session

            return success
    
    def remove_session(self, session_id: str) -> bool:
        """Remove session"""
        with self._session_lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.log_session(session_id, "移除会话")
                return True
        return False

    def delete_session(self, session_id: str) -> bool:
        """Delete session permanently (memory + database when available)"""
        with self._session_lock:
            ok = True

            if self._db:
                ok = bool(self._db.delete_session(session_id))

            if session_id in self._sessions:
                del self._sessions[session_id]

            if ok:
                logger.log_session(session_id, "删除会话")

            return ok
    
    def get_active_session_count(self) -> int:
        """Get active session count"""
        return sum(1 for s in self._sessions.values() if not s.is_finished)
    
    def get_all_sessions(self) -> List[InterviewSession]:
        """Get all sessions (from database if available)"""
        if not self.session_repo:
            return list(self._sessions.values())

        db_sessions = self.session_repo.get_all(limit=1000)
        sessions = []
        for db_session in db_sessions:
            session = self._sessions.get(db_session['session_id'])
            if not session:
                session = InterviewSession.from_db_dict(db_session)
            sessions.append(session)
        return sessions
    
    def export_session(self, session_id: str, file_path: str = None) -> Optional[str]:
        """Export session to JSON file"""
        from interview_system.services.session_exporter import export_session as export_fn

        session = self.get_session(session_id)
        if not session:
            return None

        return export_fn(
            session_id=session.session_id,
            user_name=session.user_name,
            start_time=session.start_time,
            end_time=session.end_time,
            conversation_log=session.conversation_log,
            file_path=file_path
        )

    def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        timeout = WEB_CONFIG.session_timeout
        now = datetime.now()

        expired = [
            sid for sid, session in self._sessions.items()
            if self._is_expired(session, now, timeout)
        ]

        for sid in expired:
            del self._sessions[sid]
            logger.log_session(sid, "清理过期会话")

    def _is_expired(self, session: InterviewSession, now: datetime, timeout: int) -> bool:
        """Check if session is expired"""
        try:
            start = datetime.strptime(session.start_time, "%Y-%m-%d %H:%M:%S")
            return (now - start).total_seconds() > timeout
        except ValueError as e:
            logger.warning(f"会话 {session.session_id} 时间格式错误: {e}")
            return True

    def _remove_oldest_session(self):
        """Remove oldest session"""
        if not self._sessions:
            return

        oldest_sid = min(self._sessions.keys(), key=lambda x: self._sessions[x].start_time)
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


# Convenience functions
def get_session_manager() -> SessionManager:
    """Get session manager singleton"""
    return SessionManager()

def create_session(user_name: str = None) -> InterviewSession:
    """Create new session"""
    return get_session_manager().create_session(user_name)

def get_session(session_id: str) -> Optional[InterviewSession]:
    """Get session by ID"""
    return get_session_manager().get_session(session_id)

def export_session(session_id: str, file_path: str = None) -> Optional[str]:
    """Export session to file"""
    return get_session_manager().export_session(session_id, file_path)
