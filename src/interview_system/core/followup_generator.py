#!/usr/bin/env python3
# coding: utf-8
"""
Followup Question Generator
Handles followup logic and AI generation
"""

import random
from typing import Dict, List, Tuple

import interview_system.common.logger as logger
from interview_system.common.config import INTERVIEW_CONFIG
from interview_system.integrations.api_helpers import generate_followup
from interview_system.services.session_manager import InterviewSession


class FollowupGenerator:
    """Generates followup questions based on answer quality"""

    def __init__(self):
        self.config = INTERVIEW_CONFIG

    def should_followup(
        self,
        answer: str,
        topic: Dict,
        session: InterviewSession,
        depth_score: int
    ) -> Tuple[bool, str, bool]:
        """
        Determine if followup is needed

        Returns:
            (need_followup, followup_question, is_ai_generated)
        """
        valid_answer = answer.strip()
        followup_count = session.current_followup_count
        max_followups = self.config.max_followups_per_question

        if followup_count >= max_followups:
            logger.log_interview(
                session.session_id,
                "跳过追问",
                {"reason": f"已达到最大追问次数({max_followups})", "followup_count": followup_count}
            )
            return False, "", False

        # Empty or short answer - force followup
        if not valid_answer or len(valid_answer) < self.config.min_answer_length:
            return self._generate_followup_question(
                valid_answer, topic, session, force=True
            )

        # High depth score - skip followup
        if depth_score >= self.config.max_depth_score:
            logger.log_interview(
                session.session_id,
                "跳过追问",
                {"reason": "回答详细且有深度", "depth_score": depth_score}
            )
            return False, "", False

        # Low depth - try AI followup
        return self._generate_followup_question(
            valid_answer, topic, session, force=False
        )

    def _generate_followup_question(
        self,
        answer: str,
        topic: Dict,
        session: InterviewSession,
        force: bool = False
    ) -> Tuple[bool, str, bool]:
        """
        Generate followup question

        Args:
            force: Use preset followup even if AI fails

        Returns:
            (need_followup, followup_question, is_ai_generated)
        """
        # Try AI generation
        ai_followup = generate_followup(answer, topic, session.conversation_log)

        if ai_followup:
            logger.log_interview(
                session.session_id,
                "AI追问生成成功",
                {"question": ai_followup}
            )
            return True, ai_followup, True

        # AI failed - use preset if forced
        if force:
            preset = topic.get("followups", ["能再具体说说吗？"])
            followup = random.choice(preset)
            logger.log_interview(
                session.session_id,
                "使用预设追问",
                {"question": followup}
            )
            return True, followup, False

        return False, "", False
