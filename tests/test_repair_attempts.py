from app.agent.state import AgentState
from app.agent.loop import last_test_failed

def test_edit_before_any_test_is_not_repair():
    state = AgentState(
        task="Change a function",
        repository="demo-django",
    )

    assert last_test_failed(state) is False
    assert state.repair_attempts == 0

def test_failed_test_followed_by_edit_is_repair():
    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.test_runs.append({
        "success": False,
        "stderr": "AssertionError",
    })

    assert last_test_failed(state) is True

    state.repair_attempts += 1

    state.record_repair({
        "attempt": state.repair_attempts,
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "error_type": "TEST_FAILURE",
        "action": "edit_file",
        "file": "demo-django/example.py",
        "result": "pending",
    })

    assert state.repair_attempts == 1
    assert len(state.repair_history) == 1

    repair = state.repair_history[0]

    assert repair["attempt"] == 1
    assert repair["action"] == "edit_file"
    assert repair["result"] == "pending"

def test_failed_test_does_not_increment_without_edit():
    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.test_runs.append({
        "success": False,
        "stderr": "AssertionError",
    })

    # Simulate read_file/search_code.
    action_name = "read_file"

    if action_name == "edit_file" and last_test_failed(state):
        state.repair_attempts += 1

    assert state.repair_attempts == 0

def test_two_repair_edits_count_as_two_attempts():
    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.test_runs.append({
        "success": False,
        "stderr": "AssertionError",
    })

    for action_name in ["edit_file", "edit_file"]:
        if action_name == "edit_file" and last_test_failed(state):
            state.repair_attempts += 1

            state.record_repair({
            "attempt": state.repair_attempts,
            "model": "Qwen/Qwen2.5-0.5B-Instruct",
            "error_type": "TEST_FAILURE",
            "action": "edit_file",
            "file": "demo-django/example.py",
            "result": "pending",
        })

    assert len(state.repair_history) == 2
    assert state.repair_history[0]["attempt"] == 1
    assert state.repair_history[1]["attempt"] == 2


def test_repair_history_pending_becomes_success_after_passing_tests():
    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.record_repair({
        "attempt": 1,
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "error_type": "TEST_FAILURE",
        "action": "edit_file",
        "file": "demo-django/example.py",
        "result": "pending",
    })

    assert state.repair_history[-1]["result"] == "pending"

    # Simulate successful verification.
    state.repair_history[-1]["result"] = "success"

    assert state.repair_history[-1]["result"] == "success"


def test_repair_history_pending_becomes_failed_after_failing_tests():
    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.record_repair({
        "attempt": 1,
        "model": "Qwen/Qwen2.5-0.5B-Instruct",
        "error_type": "TEST_FAILURE",
        "action": "edit_file",
        "file": "demo-django/example.py",
        "result": "pending",
    })

    assert state.repair_history[-1]["result"] == "pending"

    # Simulate failed verification.
    state.repair_history[-1]["result"] = "failed"

    assert state.repair_history[-1]["result"] == "failed"

    