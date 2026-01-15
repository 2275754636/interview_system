#!/usr/bin/env python3
# coding: utf-8
"""
Session Export Module
Handles session export and summary generation
"""

import json
import os
from datetime import datetime
from typing import Dict, Optional

import interview_system.common.logger as logger
from interview_system.common.config import EXPORT_DIR
from interview_system.services.session_manager import InterviewSession


class SessionExporter:
    """Exports sessions to JSON files"""

    def __init__(self, session_manager):
        self.session_manager = session_manager

    def export_session(self, session_id: str, file_path: str = None) -> Optional[str]:
        """
        Export session to JSON file

        Returns:
            File path on success, None on failure
        """
        session = self.session_manager.get_session(session_id)
        if not session:
            logger.warning(f"导出失败：会话 {session_id} 不存在")
            return None

        summary = self.generate_summary(session)

        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = os.path.join(
                EXPORT_DIR,
                f"interview_{session.user_name}_{timestamp}.json"
            )

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            logger.log_session(session_id, "导出会话", f"文件: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"导出会话失败: {e}")
            return None

    def generate_summary(self, session: InterviewSession) -> dict:
        """Generate session summary with statistics"""
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
