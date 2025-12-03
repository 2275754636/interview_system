#!/usr/bin/env python3
# coding: utf-8
"""
访谈核心模块 - 大学生五育并举访谈智能体
包含访谈逻辑、追问机制、回答评分等核心功能
"""

import random
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional, Tuple

import logger
from config import INTERVIEW_CONFIG
from questions import TOPICS, SCENES, EDU_TYPES
from api_client import generate_followup, is_api_available
from session_manager import InterviewSession, get_session_manager


@dataclass
class QuestionResult:
    """问题处理结果"""
    need_followup: bool = False
    followup_question: str = ""
    is_ai_generated: bool = False
    message: str = ""
    next_question: str = ""
    is_finished: bool = False


class InterviewEngine:
    """访谈引擎 - 核心访谈逻辑"""
    
    def __init__(self, session: InterviewSession):
        self.session = session
        self.config = INTERVIEW_CONFIG
        
        # 如果会话没有选题，自动选题
        if not session.selected_topics:
            session.selected_topics = self.select_questions()
    
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
        """获取当前话题"""
        idx = self.session.current_question_idx
        if idx < len(self.session.selected_topics):
            return self.session.selected_topics[idx]
        return None
    
    def score_depth(self, answer: str) -> int:
        """
        评估回答深度
        
        Args:
            answer: 用户回答
            
        Returns:
            深度分数 (0-3)
        """
        if not answer:
            return 0
        
        text = answer.lower()
        score = sum(1 for kw in self.config.depth_keywords if kw in text)
        return min(score, self.config.max_depth_score)
    
    def extract_keywords(self, answer: str) -> List[str]:
        """
        提取回答中的关键词
        
        Args:
            answer: 用户回答
            
        Returns:
            提取的关键词列表
        """
        if not answer:
            return []
        
        text = answer.lower()
        return [kw for kw in self.config.common_keywords if kw in text]
    
    def should_followup(self, answer: str, topic: Dict) -> Tuple[bool, str, bool]:
        """
        判断是否需要追问
        
        Args:
            answer: 用户回答
            topic: 当前话题
            
        Returns:
            (是否需要追问, 追问问题, 是否AI生成)
        """
        valid_answer = answer.strip()
        depth_score = self.score_depth(valid_answer)
        
        # 情况1：空回答或短回答 - 需要追问
        if not valid_answer or len(valid_answer) < self.config.min_answer_length:
            return self._generate_followup_question(valid_answer, topic, force=True)
        
        # 情况2：长回答但跑题 - 需要追问
        topic_keywords = topic["name"].split("-")
        is_on_topic = any(kw in valid_answer for kw in topic_keywords)
        
        if len(valid_answer) >= self.config.min_answer_length and not is_on_topic:
            return self._generate_followup_question(valid_answer, topic, force=True)
        
        # 情况3：回答深度满分 - 不追问
        if depth_score >= self.config.max_depth_score:
            logger.log_interview(
                self.session.session_id,
                "跳过追问",
                {"reason": "回答详细且有深度", "depth_score": depth_score}
            )
            return False, "", False
        
        # 情况4：回答深度不足 - 尝试AI追问
        return self._generate_followup_question(valid_answer, topic, force=False)
    
    def _generate_followup_question(
        self, 
        answer: str, 
        topic: Dict, 
        force: bool = False
    ) -> Tuple[bool, str, bool]:
        """
        生成追问问题
        
        Args:
            answer: 用户回答
            topic: 当前话题
            force: 是否强制追问（即使AI失败也使用预设追问）
            
        Returns:
            (是否追问, 追问问题, 是否AI生成)
        """
        # 尝试AI生成追问
        ai_followup = generate_followup(answer, topic, self.session.conversation_log)
        
        if ai_followup:
            logger.log_interview(
                self.session.session_id,
                "AI追问生成成功",
                {"question": ai_followup}
            )
            return True, ai_followup, True
        
        # AI失败时的处理
        if force:
            # 强制追问模式：使用预设追问
            preset = topic.get("followups", ["能再具体说说吗？"])
            followup = random.choice(preset)
            logger.log_interview(
                self.session.session_id,
                "使用预设追问",
                {"question": followup}
            )
            return True, followup, False
        
        # 非强制模式：不追问
        return False, "", False
    
    def process_answer(self, answer: str) -> QuestionResult:
        """
        处理用户回答
        
        Args:
            answer: 用户回答
            
        Returns:
            处理结果
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
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not self.session.is_followup:
            # 处理核心问题回答
            depth = self.score_depth(answer)
            valid_answer = answer.strip() or "用户未给出有效回答"
            
            # 记录回答
            log_entry = {
                "timestamp": timestamp,
                "topic": current_topic["name"],
                "question_type": "核心问题",
                "question": current_topic["questions"][0],
                "answer": valid_answer,
                "depth_score": depth
            }
            self.session.conversation_log.append(log_entry)
            
            logger.log_interview(
                self.session.session_id,
                "记录核心问题回答",
                {"topic": current_topic["name"], "depth": depth}
            )
            
            # 判断是否需要追问
            need_followup, followup_q, is_ai = self.should_followup(answer, current_topic)
            
            if need_followup:
                self.session.is_followup = True
                result.need_followup = True
                result.followup_question = followup_q
                result.is_ai_generated = is_ai
                result.message = "请补充回答"
                return result
            
            # 不需要追问，进入下一题
            return self._move_to_next_question(result)
        
        else:
            # 处理追问回答
            log_entry = {
                "timestamp": timestamp,
                "topic": current_topic["name"],
                "question_type": "追问回答",
                "question": "（上轮追问）",
                "answer": answer.strip() or "用户未补充回答",
                "depth_score": self.score_depth(answer)
            }
            self.session.conversation_log.append(log_entry)
            
            logger.log_interview(
                self.session.session_id,
                "记录追问回答",
                {"topic": current_topic["name"]}
            )
            
            self.session.is_followup = False
            return self._move_to_next_question(result)
    
    def _move_to_next_question(self, result: QuestionResult) -> QuestionResult:
        """移动到下一题"""
        self.session.current_question_idx += 1
        
        if self.session.current_question_idx >= self.config.total_questions:
            self.session.is_finished = True
            self.session.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result.is_finished = True
            result.message = "访谈结束"
            
            logger.log_interview(self.session.session_id, "访谈结束")
        else:
            result.next_question = self.get_current_question()
            result.message = "进入下一题"
        
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
