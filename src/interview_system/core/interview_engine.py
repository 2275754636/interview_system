#!/usr/bin/env python3
# coding: utf-8
"""
Interview Engine - Orchestrates interview flow
Delegates answer processing and followup generation
"""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import interview_system.common.logger as logger
from interview_system.common.config import INTERVIEW_CONFIG
from interview_system.core.answer_processor import AnswerProcessor
from interview_system.core.followup_generator import FollowupGenerator
from interview_system.core.questions import TOPICS, SCENES, EDU_TYPES
from interview_system.integrations.api_helpers import is_api_available
from interview_system.services.session_manager import InterviewSession, get_session_manager


@dataclass
class QuestionResult:
    """Question processing result"""
    need_followup: bool = False
    followup_question: str = ""
    is_ai_generated: bool = False
    message: str = ""
    next_question: str = ""
    is_finished: bool = False


class InterviewEngine:
    """Interview orchestrator - delegates to processors"""

    def __init__(self, session: InterviewSession):
        self.session = session
        self.config = INTERVIEW_CONFIG
        self.answer_processor = AnswerProcessor()
        self.followup_generator = FollowupGenerator()

        if not session.selected_topics:
            session.selected_topics = self.select_questions()
            get_session_manager().update_session(session)
    
    def select_questions(self) -> List[Dict]:
        """
        选择访谈问题
        规则：随机选6题，覆盖学校/家庭/社区三场景 + 德/智/体/美/劳五育
        
        Returns:
            选中的话题列表
        """
        # 按场景分组
        scene_groups = {scene: [] for scene in SCENES}
        for topic in TOPICS:
            scene_groups[topic["scene"]].append(topic)
        
        # 按五育分组
        edu_groups = {edu: [] for edu in EDU_TYPES}
        for topic in TOPICS:
            edu_groups[topic["edu_type"]].append(topic)
        
        selected = []
        
        # 三场景各选1题（确保覆盖所有场景）
        for scene in SCENES:
            if scene_groups[scene]:
                selected.append(random.choice(scene_groups[scene]))
        
        # 检查已选题目覆盖的五育
        covered_edu = set(t["edu_type"] for t in selected)
        needed_edu = set(EDU_TYPES) - covered_edu
        
        # 补全缺失的五育维度
        while needed_edu and len(selected) < self.config.total_questions:
            edu_type = needed_edu.pop()
            candidates = [t for t in edu_groups[edu_type] if t not in selected]
            if candidates:
                selected.append(random.choice(candidates))
        
        # 补全剩余题目
        remaining = [t for t in TOPICS if t not in selected]
        while len(selected) < self.config.total_questions and remaining:
            topic = random.choice(remaining)
            selected.append(topic)
            remaining.remove(topic)
        
        # 打乱顺序
        random.shuffle(selected)
        
        logger.log_interview(
            self.session.session_id, 
            "选题完成", 
            {"count": len(selected), "topics": [t["name"] for t in selected]}
        )
        
        return selected
    
    def get_current_question(self) -> str:
        """
        获取当前问题
        
        Returns:
            当前问题文本
        """
        if self.session.is_finished:
            return "访谈已结束，感谢参与！"
        
        idx = self.session.current_question_idx
        if idx >= len(self.session.selected_topics):
            return "访谈已结束，感谢参与！"
        
        topic = self.session.selected_topics[idx]
        
        if self.session.is_followup:
            return "请针对刚才的问题补充更多细节..."
        
        question = topic["questions"][0]
        total = self.config.total_questions
        
        return f"【第{idx + 1}/{total}题】{topic['name']}:\n{question}"
    
    def get_current_topic(self) -> Optional[Dict]:
        """Get current topic"""
        idx = self.session.current_question_idx
        if idx < len(self.session.selected_topics):
            return self.session.selected_topics[idx]
        return None

    def process_answer(self, answer: str) -> QuestionResult:
        """
        Process user answer - delegates to processors

        Returns:
            Processing result
        """
        result = QuestionResult()

        if self.session.is_finished:
            result.is_finished = True
            result.message = "访谈已结束"
            return result

        current_topic = self.get_current_topic()
        if not current_topic:
            result.is_finished = True
            result.message = "访谈已结束"
            return result

        if not self.session.is_followup:
            return self._process_core_answer(answer, current_topic, result)

        return self._process_followup_answer(answer, current_topic, result)

    def _process_core_answer(
        self,
        answer: str,
        topic: Dict,
        result: QuestionResult
    ) -> QuestionResult:
        """Process core question answer"""
        log_entry = self.answer_processor.process_core_answer(
            self.session, answer, topic
        )
        self.session.conversation_log.append(log_entry)

        logger.log_interview(
            self.session.session_id,
            "记录核心问题回答",
            {"topic": topic["name"], "depth": log_entry["depth_score"]}
        )

        depth = log_entry["depth_score"]
        need_followup, followup_q, is_ai = self.followup_generator.should_followup(
            answer, topic, self.session, depth
        )

        if need_followup:
            self.session.is_followup = True
            self.session.current_followup_is_ai = is_ai
            self.session.current_followup_count = 1
            self.session.current_followup_question = followup_q
            get_session_manager().update_session(self.session)
            result.need_followup = True
            result.followup_question = followup_q
            result.is_ai_generated = is_ai
            result.message = "请补充回答"
            return result

        return self._move_to_next_question(result)

    def _process_followup_answer(
        self,
        answer: str,
        topic: Dict,
        result: QuestionResult
    ) -> QuestionResult:
        """Process followup answer"""
        log_entry = self.answer_processor.process_followup_answer(
            self.session, answer, topic
        )
        self.session.conversation_log.append(log_entry)

        logger.log_interview(
            self.session.session_id,
            "记录追问回答",
            {"topic": topic["name"], "followup_count": self.session.current_followup_count}
        )

        depth = log_entry["depth_score"]
        need_more_followup, followup_q, is_ai = self.followup_generator.should_followup(
            answer, topic, self.session, depth
        )

        if need_more_followup:
            self.session.current_followup_count += 1
            self.session.current_followup_is_ai = is_ai
            self.session.current_followup_question = followup_q
            get_session_manager().update_session(self.session)
            result.need_followup = True
            result.followup_question = followup_q
            result.is_ai_generated = is_ai
            result.message = "请继续补充"
            return result

        self.session.is_followup = False
        self.session.current_followup_count = 0
        self.session.current_followup_question = ""
        self.session.current_followup_is_ai = False
        return self._move_to_next_question(result)
    
    def _move_to_next_question(self, result: QuestionResult) -> QuestionResult:
        """移动到下一题"""
        self.session.current_question_idx += 1
        self.session.current_followup_count = 0  # 重置追问计数
        self.session.current_followup_is_ai = False
        self.session.current_followup_question = ""
        self.session.is_followup = False
        
        if self.session.current_question_idx >= self.config.total_questions:
            self.session.is_finished = True
            self.session.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.is_finished = True
            result.message = "访谈结束"
            
            logger.log_interview(self.session.session_id, "访谈结束")
        else:
            result.next_question = self.get_current_question()
            result.message = "进入下一题"

        get_session_manager().update_session(self.session)
        
        return result
    
    def skip_question(self) -> QuestionResult:
        """
        跳过当前问题
        
        Returns:
            处理结果
        """
        result = QuestionResult()
        current_topic = self.get_current_topic()
        
        if current_topic:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = {
                "timestamp": timestamp,
                "topic": current_topic["name"],
                "question_type": "核心问题",
                "question": current_topic["questions"][0],
                "answer": "用户选择跳过",
                "depth_score": 0
            }
            self.session.conversation_log.append(log_entry)
            
            logger.log_interview(
                self.session.session_id,
                "跳过问题",
                {"topic": current_topic["name"]}
            )
        
        self.session.is_followup = False
        return self._move_to_next_question(result)

    def skip_round(self) -> QuestionResult:
        """
        跳过本轮对话

        语义：
        - 若当前处于追问状态：跳过追问轮次并直接进入下一题
        - 否则：等价于跳过当前题（核心题）

        Returns:
            处理结果
        """
        if not self.session.is_followup:
            return self.skip_question()

        result = QuestionResult()
        current_topic = self.get_current_topic()

        if current_topic:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            last_followup_q = self.session.current_followup_question or '（追问）'
            log_entry = {
                "timestamp": timestamp,
                "topic": current_topic["name"],
                "question_type": "追问跳过",
                "question": last_followup_q,
                "answer": "用户选择跳过追问",
                "depth_score": 0,
                "is_ai_generated": self.session.current_followup_is_ai
            }
            get_session_manager().add_conversation_log(self.session.session_id, log_entry)

            logger.log_interview(
                self.session.session_id,
                "跳过追问轮次",
                {"topic": current_topic["name"]}
            )

        self.session.is_followup = False
        self.session.current_followup_count = 0
        self.session.current_followup_question = ""
        return self._move_to_next_question(result)
    
    def get_summary(self) -> Dict:
        """
        获取访谈摘要
        
        Returns:
            访谈摘要字典
        """
        scene_stats = {}
        edu_stats = {}
        followup_stats = {"预设追问": 0, "AI智能追问": 0}
        
        for log in self.session.conversation_log:
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
            "session_id": self.session.session_id,
            "user_name": self.session.user_name,
            "start_time": self.session.start_time,
            "end_time": self.session.end_time or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "api_enabled": is_api_available(),
            "statistics": {
                "total_logs": len(self.session.conversation_log),
                "scene_distribution": scene_stats,
                "edu_distribution": edu_stats,
                "followup_distribution": followup_stats
            },
            "conversation_log": self.session.conversation_log
        }


# ----------------------------
# 便捷函数
# ----------------------------
def create_interview(user_name: str = None) -> Tuple[InterviewSession, InterviewEngine]:
    """
    创建新的访谈
    
    Args:
        user_name: 用户名
        
    Returns:
        (会话对象, 访谈引擎)
    """
    session = get_session_manager().create_session(user_name)
    engine = InterviewEngine(session)
    return session, engine


def get_interview_engine(session: InterviewSession) -> InterviewEngine:
    """
    获取访谈引擎
    
    Args:
        session: 会话对象
        
    Returns:
        访谈引擎
    """
    return InterviewEngine(session)
