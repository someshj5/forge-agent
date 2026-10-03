from app.agent.state import AgentState


def test_repair_history_starts_empty():
    state = AgentState(
        task="Rename variable x to y",
        repository="demo-django",
    )

    assert state.repair_attempts == 0
    assert state.repair_history == []


def test_record_repair():
    state = AgentState(
        task="Rename variable x to y",
        repository="demo-django",
    )

    repair = {
        "attempt": 1,
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "error_type": "TEST_FAILURE",
        "action": "edit_file",
        "file": "demo-django/example.py",
        "result": "pending",
    }

    state.record_repair(repair)

    assert len(state.repair_history) == 1
    assert state.repair_history[0] == repair