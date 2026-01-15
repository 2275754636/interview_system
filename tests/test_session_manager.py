import json

from interview_system.services.session_manager import get_session_manager


def test_export_session_writes_json_summary(isolated_runtime):
    sm = get_session_manager()
    session = sm.create_session("tester")

    sm.add_conversation_log(
        session.session_id,
        {
            "timestamp": "2025-01-01 00:00:00",
            "topic": "学校-德育",
            "question_type": "核心问题",
            "question": "Q",
            "answer": "A",
            "depth_score": 1,
        },
    )

    output_file = isolated_runtime["tmp_path"] / "export.json"
    path = sm.export_session(session.session_id, file_path=str(output_file))
    assert path == str(output_file)

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert data["session_id"] == session.session_id
    assert data["user_name"] == session.user_name
    assert "statistics" in data
    assert data["statistics"]["total_logs"] == 1
    assert isinstance(data["conversation_log"], list)


def test_get_session_loads_from_database_when_not_in_memory(isolated_runtime):
    sm = get_session_manager()
    session = sm.create_session("tester")
    sm.add_conversation_log(
        session.session_id,
        {
            "timestamp": "2025-01-01 00:00:00",
            "topic": "学校-德育",
            "question_type": "核心问题",
            "question": "Q",
            "answer": "A",
            "depth_score": 1,
        },
    )

    # 清空内存缓存，验证能从数据库加载（isolated_runtime fixture 将 DB 指向临时目录）
    sm._sessions.pop(session.session_id)

    loaded = sm.get_session(session.session_id)
    assert loaded is not None
    assert loaded.session_id == session.session_id
    assert len(loaded.conversation_log) == 1


def test_rollback_session_restores_logs_and_state(isolated_runtime, monkeypatch):
    import interview_system.integrations.api_helpers as api_helpers
    from interview_system.core.interview_engine import InterviewEngine

    monkeypatch.setattr(api_helpers, "generate_followup", lambda *_args, **_kwargs: None, raising=True)

    sm = get_session_manager()
    session = sm.create_session("tester")
    engine = InterviewEngine(session)

    state_before = {
        "session_id": session.session_id,
        "current_question_idx": session.current_question_idx,
        "is_finished": session.is_finished,
        "end_time": session.end_time,
        "is_followup": session.is_followup,
        "current_followup_is_ai": session.current_followup_is_ai,
        "current_followup_count": session.current_followup_count,
        "current_followup_question": session.current_followup_question,
    }
    log_count_before = len(session.conversation_log)

    # 触发一次操作：写入核心回答并进入追问态
    r1 = engine.process_answer("短")
    assert r1.need_followup is True
    assert len(session.conversation_log) == log_count_before + 1
    assert session.is_followup is True

    ok = sm.rollback_session(
        session.session_id,
        target_log_count=log_count_before,
        session_state=state_before
    )
    assert ok is True
    assert len(session.conversation_log) == log_count_before
    assert session.is_followup is False
