import interview_system.core.interview_engine as interview_engine
import interview_system.integrations.api_helpers as api_helpers
from interview_system.core.interview_engine import InterviewEngine
from interview_system.services.session_manager import InterviewSession, get_session_manager


def test_select_questions_covers_all_scenes(isolated_runtime, monkeypatch):
    monkeypatch.setattr(api_helpers, "generate_followup", lambda *_args, **_kwargs: None, raising=True)

    session = get_session_manager().create_session("tester")
    engine = InterviewEngine(session)

    selected = session.selected_topics
    assert len(selected) == engine.config.total_questions

    scenes = {t["scene"] for t in selected}
    assert {"学校", "家庭", "社区"}.issubset(scenes)


def test_process_answer_appends_core_log_and_advances_or_followups(isolated_runtime, monkeypatch):
    monkeypatch.setattr(api_helpers, "generate_followup", lambda *_args, **_kwargs: None, raising=True)

    session = get_session_manager().create_session("tester")
    engine = InterviewEngine(session)

    # 触发强制追问（短回答）
    result = engine.process_answer("太短")
    assert result.need_followup is True
    assert session.is_followup is True

    # 追问回答（仍然短，可能继续追问，但不应崩溃）
    result2 = engine.process_answer("补充")
    assert isinstance(result2.need_followup, bool)

    # 日志至少包含：核心问题一条 + 追问回答一条
    assert len(session.conversation_log) >= 2


def test_skip_question_writes_log_and_moves_next(isolated_runtime, monkeypatch):
    monkeypatch.setattr(api_helpers, "generate_followup", lambda *_args, **_kwargs: None, raising=True)

    session = InterviewSession(session_id="s1", user_name="tester")
    # 通过 SessionManager 管理该会话，保证写日志路径一致
    sm = get_session_manager()
    sm._sessions[session.session_id] = session

    engine = InterviewEngine(session)
    before_idx = session.current_question_idx

    result = engine.skip_question()
    assert session.current_question_idx == before_idx + 1
    assert len(session.conversation_log) == 1
    assert session.conversation_log[0]["answer"] == "用户选择跳过"
    assert result.is_finished in (True, False)


def test_skip_round_in_followup_skips_followup_and_moves_next(isolated_runtime, monkeypatch):
    monkeypatch.setattr(api_helpers, "generate_followup", lambda *_args, **_kwargs: None, raising=True)

    sm = get_session_manager()
    session = sm.create_session("tester")
    engine = InterviewEngine(session)

    # 触发追问态
    result = engine.process_answer("短")
    assert result.need_followup is True
    assert session.is_followup is True

    before_idx = session.current_question_idx
    r2 = engine.skip_round()

    assert session.is_followup is False
    assert session.current_question_idx == before_idx + 1
    assert len(session.conversation_log) == 2  # 核心回答 + 追问跳过
    assert session.conversation_log[1]["question_type"] == "追问跳过"
    assert r2.is_finished in (True, False)
