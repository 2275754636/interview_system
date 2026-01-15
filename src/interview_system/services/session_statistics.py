#!/usr/bin/env python3
# coding: utf-8
"""
Session Statistics Module
Handles session analytics and statistics
"""

from typing import Dict, List


class SessionStatistics:
    """Provides session statistics and analytics"""

    def __init__(self, session_manager):
        self.session_manager = session_manager

    def get_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get statistics for date range

        Returns:
            Statistics dictionary
        """
        if self.session_manager._db:
            return self.session_manager._db.get_statistics_by_date_range(start_date, end_date)

        # Fallback: calculate from memory
        sessions = self.session_manager._sessions
        total = len(sessions)
        finished = sum(1 for s in sessions.values() if s.is_finished)
        return {
            'total_sessions': total,
            'finished_sessions': finished,
            'completion_rate': round(finished / total * 100, 1) if total > 0 else 0,
            'scene_distribution': {},
            'edu_distribution': {},
            'followup_distribution': {},
            'avg_depth_score': 0
        }

    def get_daily_statistics(self, days: int = 7) -> List[Dict]:
        """
        Get daily statistics for recent N days

        Returns:
            List of daily statistics
        """
        if self.session_manager._db:
            return self.session_manager._db.get_daily_statistics(days)
        return []

    def get_session_count(self) -> int:
        """Get total session count"""
        if self.session_manager._db:
            return self.session_manager._db.get_session_count()
        return len(self.session_manager._sessions)
