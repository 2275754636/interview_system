"""Dependency injection for FastAPI"""

from functools import lru_cache
from interview_system.services.session_manager import SessionManager


@lru_cache()
def get_session_manager() -> SessionManager:
    """Get singleton session manager"""
    return SessionManager()
