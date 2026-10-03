from unittest.mock import Mock, patch

from app.agent.loop import AgentLoop

small_model = Mock()
strong_model = Mock()

small_model.generate.side_effect = [
    '{"action": "run_tests", "arguments": {"project_path": "demo-django"}}',
    '{"action": "edit_file", "arguments": {"path": "...", "old_text": "...", "new_text": "..."}}',
]

strong_model.generate.return_value = (
    '{"action": "final", "arguments": '
    '{"message": "Completed after escalation."}}'
)

manager = Mock()


def test_runtime_model_escalation():
    small_model = Mock()
    strong_model = Mock()

    small_model.generate.side_effect = [
        '{"action": "run_tests", "arguments": {"project_path": "demo-django"}}',
        '{"action": "edit_file", "arguments": {"path": "demo-django/example.py", "old_text": "old", "new_text": "new"}}',
    ]

    strong_model.generate.return_value = (
        '{"action": "final", "arguments": '
        '{"message": "Completed after escalation."}}'
    )

    manager = Mock()
    manager.get_model.side_effect = [
        small_model,
        small_model,
        strong_model,
    ]

    fake_test_result = {
        "success": False,
        "exit_code": 1,
        "stdout": "",
        "stderr": "AssertionError: expected 2, got 3",
    }

    fake_edit_result = {
        "success": True,
        "path": "demo-django/example.py",
        "message": "File edited successfully.",
    }

    with patch.dict(
        "app.agent.loop.TOOLS",
        {
            "run_tests": Mock(return_value=fake_test_result),
            "edit_file": Mock(return_value=fake_edit_result),
        },
    ):
        agent = AgentLoop(
            llm=None,
            model_manager=manager,
        )

        state = agent.run(
            task="Rename variable x to y",
            repository="demo-django",
        )

    assert state.status == "completed"
    assert state.repair_attempts == 1

    assert state.current_model == "Qwen/Qwen2.5-1.5B-Instruct"

    assert manager.get_model.call_args_list[0].args[0] == (
        "Qwen/Qwen2.5-0.5B-Instruct"
    )

    assert manager.get_model.call_args_list[1].args[0] == (
        "Qwen/Qwen2.5-0.5B-Instruct"
    )

    assert manager.get_model.call_args_list[2].args[0] == (
        "Qwen/Qwen2.5-1.5B-Instruct"
    )