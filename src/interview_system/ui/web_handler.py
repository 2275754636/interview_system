#!/usr/bin/env python3
# coding: utf-8
"""
Interview Handler Module
Handles web interview session logic
"""

import copy
from typing import List, Optional, Tuple

import interview_system.common.logger as logger
from interview_system.core.interview_engine import InterviewEngine, create_interview
from interview_system.services.session_manager import InterviewSession, get_session_manager
from interview_system.ui.web_utils import format_dict

try:
    import gradio as gr
    GRADIO_AVAILABLE = True
except ImportError:
    GRADIO_AVAILABLE = False
    gr = None


class InterviewHandler:
    """Handles single user interview session"""

    def __init__(self):
        self.session: Optional[InterviewSession] = None
        self.engine: Optional[InterviewEngine] = None
        self._initialized = False
        self._undo_stack = []

    def _capture_session_state(self) -> dict:
        """Capture session state snapshot for rollback"""
        if not self.session:
            return {}
        return {
            "session_id": self.session.session_id,
            "current_question_idx": self.session.current_question_idx,
            "is_finished": self.session.is_finished,
            "end_time": self.session.end_time,
            "is_followup": self.session.is_followup,
            "current_followup_is_ai": self.session.current_followup_is_ai,
            "current_followup_count": self.session.current_followup_count,
            "current_followup_question": self.session.current_followup_question,
        }

    def _push_undo_snapshot(self, history: List, submitted_text: str):
        """Push undo snapshot for state-changing operations"""
        if not self.session:
            return
        snapshot = {
            "history_before": copy.deepcopy(history),
            "submitted_text": submitted_text,
            "session_state_before": self._capture_session_state(),
            "log_count_before": len(self.session.conversation_log) if self.session.conversation_log else 0,
        }
        self._undo_stack.append(snapshot)

    def initialize(self, user_name: str = None) -> Tuple[List, str]:
        """
        Initialize interview session

        Returns:
            (chat_history, status_message)
        """
        self.session, self.engine = create_interview(user_name or "Web访谈者")
        self._initialized = True

        first_question = self.engine.get_current_question()

        welcome = (
            "👋 你好，欢迎参加本次访谈！\n\n"
            "接下来我会向你提出 6 个问题，话题涉及你在学校、家庭和社区中的经历与感受。\n\n"
            "💬 请放松心情，用自己的话分享真实想法，没有标准答案。\n"
            "⏭️ 如果某个问题不方便回答，可以点击「跳过」按钮。\n\n"
            "准备好了吗？让我们开始吧！"
        )

        history = [
            [None, welcome],
            [None, first_question]
        ]

        logger.log_interview(
            self.session.session_id,
            "Web访谈开始",
            {"user": self.session.user_name}
        )

        return history, ""

    def lazy_initialize(self) -> Tuple[List, str]:
        """
        Lazy initialize - create session and show first question

        Returns:
            (chat_history, status_message)
        """
        return self.initialize("Web访谈者")

    def process_message(
        self,
        user_input: str,
        history: List
    ) -> Tuple[List, str, dict]:
        """
        Process user message

        Returns:
            (updated_history, clear_input_value, input_update)
        """
        if not self._initialized or not self.session or not self.engine:
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        if self.session.is_finished:
            history.append([user_input, "访谈已结束，请点击下方按钮开始新访谈。"])
            return history, "", gr.update(interactive=False) if GRADIO_AVAILABLE else {}

        if not user_input.strip():
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        # Handle skip command
        if user_input.strip() in ["/跳过", "跳过", "/skip"]:
            return self._handle_skip_command(user_input, history)

        # Handle normal answer
        self._push_undo_snapshot(history, submitted_text=user_input)
        result = self.engine.process_answer(user_input)

        history.append([user_input, None])

        if result.need_followup:
            prefix = "💡 " if result.is_ai_generated else "📝 "
            history[-1][1] = "收到。"
            history.append([None, f"{prefix}{result.followup_question}"])
        elif result.is_finished:
            self.export_log()
            history[-1][1] = "收到。"
            history.append([None, "🎉 访谈结束！感谢你的参与。"])
            return history, "", gr.update(interactive=False) if GRADIO_AVAILABLE else {}
        else:
            history[-1][1] = "✅ 收到，进入下一题。"
            history.append([None, result.next_question])

        return history, "", gr.update() if GRADIO_AVAILABLE else {}

    def _handle_skip_command(self, user_input: str, history: List) -> Tuple[List, str, dict]:
        """Handle skip command"""
        was_followup = self.session.is_followup
        self._push_undo_snapshot(history, submitted_text="")
        result = self.engine.skip_round()

        if was_followup:
            history.append([user_input, "好的，已跳过本轮追问。"])
        else:
            history.append([user_input, "好的，已跳过当前问题。"])

        if result.is_finished:
            self.export_log()
            history.append([None, "🎉 访谈结束！感谢你的参与。"])
            return history, "", gr.update(interactive=False) if GRADIO_AVAILABLE else {}

        history.append([None, result.next_question])
        return history, "", gr.update() if GRADIO_AVAILABLE else {}

    def skip_round(self, history: List) -> Tuple[List, str, dict]:
        """
        Skip current round (question or followup)

        Returns:
            (updated_history, clear_input_value, input_update)
        """
        if not self._initialized or not self.session or not self.engine:
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        if self.session.is_finished:
            history.append([None, "访谈已结束，请点击下方按钮开始新访谈。"])
            return history, "", gr.update(interactive=False) if GRADIO_AVAILABLE else {}

        was_followup = self.session.is_followup
        self._push_undo_snapshot(history, submitted_text="")
        result = self.engine.skip_round()

        if was_followup:
            history.append([None, "好的，已跳过本轮追问。"])
        else:
            history.append([None, "好的，已跳过当前问题。"])

        if result.is_finished:
            self.export_log()
            history.append([None, "🎉 访谈结束！感谢你的参与。"])
            return history, "", gr.update(interactive=False, value="") if GRADIO_AVAILABLE else {}

        if result.next_question:
            history.append([None, result.next_question])
        return history, "", gr.update(value="") if GRADIO_AVAILABLE else {}

    def undo_last(self, history: List) -> Tuple[List, str, dict]:
        """
        Undo last operation (send/skip)

        Returns:
            (rolled_back_history, restored_input_value, input_update)
        """
        if not self._initialized or not self.session or not self.engine:
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        if not self._undo_stack:
            history.append([None, "暂无可撤回内容。"])
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        snapshot = self._undo_stack[-1]
        session_id = snapshot.get("session_state_before", {}).get("session_id")
        target_log_count = int(snapshot.get("log_count_before", 0))
        session_state = snapshot.get("session_state_before", {})

        ok = get_session_manager().rollback_session(
            session_id,
            target_log_count=target_log_count,
            session_state=session_state
        )
        if not ok:
            history.append([None, "撤回失败：数据回滚未成功，请稍后重试。"])
            return history, "", gr.update() if GRADIO_AVAILABLE else {}

        self._undo_stack.pop()

        restored_history = snapshot.get("history_before", history)
        restored_text = snapshot.get("submitted_text", "") or ""
        interactive = not bool(session_state.get("is_finished", False))
        return restored_history, restored_text, gr.update(value=restored_text, interactive=interactive) if GRADIO_AVAILABLE else {}

    def export_log(self) -> Optional[str]:
        """
        Export interview log

        Returns:
            Exported file path
        """
        if not self.session:
            return None

        return get_session_manager().export_session(self.session.session_id)

    def get_statistics(self) -> str:
        """
        Get interview statistics

        Returns:
            Statistics text
        """
        if not self.session or not self.engine:
            return "暂无统计信息"

        summary = self.engine.get_summary()
        stats = summary.get("statistics", {})

        text = f"""
📊 **访谈统计**

- 会话ID: {summary.get('session_id', 'N/A')}
- 用户: {summary.get('user_name', 'N/A')}
- 开始时间: {summary.get('start_time', 'N/A')}
- 总记录数: {stats.get('total_logs', 0)}

**场景分布:**
{format_dict(stats.get('scene_distribution', {}))}

**五育分布:**
{format_dict(stats.get('edu_distribution', {}))}

**追问统计:**
{format_dict(stats.get('followup_distribution', {}))}
"""
        return text.strip()
