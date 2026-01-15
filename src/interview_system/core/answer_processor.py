#!/usr/bin/env python3
# coding: utf-8
"""
Answer Processing Module
Handles answer evaluation and logging
"""

from datetime import datetime
from typing import Dict, List

from interview_system.common.config import INTERVIEW_CONFIG
from interview_system.services.session_manager import InterviewSession


class AnswerProcessor:
    """Processes and evaluates user answers"""

    def __init__(self):
        self.config = INTERVIEW_CONFIG

    def score_depth(self, answer: str) -> int:
        """
        Evaluate answer depth

        Returns:
            Depth score (0-3)
        """
        if not answer:
            return 0

        text = answer.lower()
        score = sum(1 for kw in self.config.depth_keywords if kw in text)
        return min(score, self.config.max_depth_score)

    def extract_keywords(self, answer: str) -> List[str]:
        """Extract keywords from answer"""
        if not answer:
            return []

        text = answer.lower()
        return [kw for kw in self.config.common_keywords if kw in text]

    def process_core_answer(
        self,
        session: InterviewSession,
        answer: str,
        topic: Dict
    ) -> Dict:
        """
        Process core question answer

        Returns:
            Log entry dict
        """
        depth = self.score_depth(answer)
        valid_answer = answer.strip() or "用户未给出有效回答"

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": topic["name"],
            "question_type": "核心问题",
            "question": topic["questions"][0],
            "answer": valid_answer,
            "depth_score": depth
        }

    def process_followup_answer(
        self,
        session: InterviewSession,
        answer: str,
        topic: Dict
    ) -> Dict:
        """
        Process followup answer

        Returns:
            Log entry dict
        """
        is_ai_followup = session.current_followup_is_ai
        last_followup_q = session.current_followup_question or '（追问）'

        return {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "topic": topic["name"],
            "question_type": "追问回答",
            "question": last_followup_q,
            "answer": answer.strip() or "用户未补充回答",
            "depth_score": self.score_depth(answer),
            "is_ai_generated": is_ai_followup
        }
