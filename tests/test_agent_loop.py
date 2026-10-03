from app.agent.loop import AgentLoop
from unittest.mock import patch
from unittest.mock import Mock

class FakeLLM:

    def __init__(self):
        self.calls = 0

    def generate(self, messages, **kwargs):
        self.calls += 1

        if self.calls == 1:
            return (
                '{"action":"search_code",'
                '"arguments":{'
                '"query":"urlpatterns",'
                '"path":"demo-django"'
                '}}'
            )

        return (
            '{"action":"final",'
            '"arguments":{'
            '"message":"Found the Django URL configuration."'
            '}}'
        )


def test_agent_loop_executes_tool():

    llm = FakeLLM()

    agent = AgentLoop(
        llm=llm,
        max_iterations=5,
    )

    state = agent.run(
        task="Find where Django URL routes are defined.",
        repository="demo-django",
    )

    assert state.status == "completed"

    assert state.final_message == (
        "Found the Django URL configuration."
    )

    assert len(state.tool_calls) == 1

    assert state.tool_calls[0]["action"] == "search_code"

    assert state.tool_calls[0]["result"]["success"] is True


def test_agent_loop_stops_after_invalid_action_budget():
    class InvalidLLM:
        def generate(self, messages, **kwargs):
            return '{"action":"invalid_action","arguments":{}}'

    llm = InvalidLLM()

    agent = AgentLoop(
        llm=llm,
        max_iterations=10,
        max_invalid_actions=2,
    )

    state = agent.run(
        task="Find urlpatterns.",
        repository="demo-django",
    )

    assert state.status == "failed"
    assert state.invalid_actions == 2
    assert state.iteration == 2
    assert state.final_message == (
        "Agent stopped because the maximum number of "
        "invalid actions was reached."
    )

def test_agent_loop_stops_after_tool_failure_budget():
    class ToolFailureLLM:
        def generate(self, messages, **kwargs):
            return (
                '{"action":"read_file",'
                '"arguments":{"path":"demo-django/missing.py"}}'
            )

    llm = ToolFailureLLM()

    agent = AgentLoop(
        llm=llm,
        max_iterations=10,
        max_tool_failures=2,
    )

    state = agent.run(
        task="Find a missing file.",
        repository="demo-django",
    )

    assert state.status == "failed"
    assert state.tool_failures == 2
    assert state.iteration == 2
    assert state.final_message == (
        "Agent stopped because the maximum number of "
        "tool failures was reached."
    )

def test_agent_recovers_from_failed_tool():
    class RecoveryLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"read_file",'
                    '"arguments":{"path":"demo-django/missing.py"}}'
                )

            if self.calls == 2:
                return (
                    '{"action":"search_code",'
                    '"arguments":{"query":"missing.py",'
                    '"path":"demo-django"}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Recovered by searching the repository."}}'
            )

    llm = RecoveryLLM()

    agent = AgentLoop(
        llm=llm,
        max_iterations=5,
        max_tool_failures=3,
    )

    state = agent.run(
        task="Find the missing file.",
        repository="demo-django",
    )

    assert state.status == "completed"
    assert state.tool_failures == 1
    assert len(state.tool_calls) == 2
    assert state.tool_calls[0]["result"]["success"] is False
    assert state.tool_calls[1]["result"]["success"] is True


def test_agent_state_tracks_repair_information():
    from app.agent.state import AgentState

    state = AgentState(
        task="Fix failing test",
        repository="demo-django",
    )

    state.plan.append("Inspect failing test")
    state.relevant_files.append("demo-django/app/views.py")
    state.edits.append({
        "path": "demo-django/app/views.py",
    })
    state.test_runs.append({
        "success": False,
    })
    state.errors.append({
        "type": "TEST_FAILURE",
        "message": "Expected 200, got 500",
    })
    state.repair_attempts += 1

    assert state.plan == ["Inspect failing test"]
    assert state.relevant_files == [
        "demo-django/app/views.py"
    ]
    assert len(state.edits) == 1
    assert len(state.test_runs) == 1
    assert state.errors[0]["type"] == "TEST_FAILURE"
    assert state.repair_attempts == 1

def test_agent_loop_records_test_results():
    class TestLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Tests completed."}}'
            )

    llm = TestLLM()

    agent = AgentLoop(
        llm=llm,
        max_iterations=5,
    )

    state = agent.run(
        task="Run the tests.",
        repository="demo-django",
    )

    assert state.status == "completed"
    assert len(state.test_runs) == 1
    assert state.test_runs[0]["success"] is True
    assert state.errors == []


def test_agent_loop_records_successful_repair_history():
    class RepairLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            if self.calls == 2:
                return (
                    '{"action":"edit_file",'
                    '"arguments":{'
                    '"path":"demo-django/app/views.py",'
                    '"old_text":"return 500",'
                    '"new_text":"return 200"'
                    '}}'
                )

            if self.calls == 3:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Repair completed."}}'
            )

    llm = RepairLLM()

    run_tests_calls = 0

    def fake_run_tests(project_path):
        nonlocal run_tests_calls

        run_tests_calls += 1

        if run_tests_calls == 1:
            return {
                "success": False,
                "stderr": "AssertionError",
            }

        return {
            "success": True,
            "stdout": "1 passed",
        }

    def fake_edit_file(path, old_text, new_text):
        return {
            "success": True,
            "path": path,
        }

    with patch(
        "app.agent.loop.TOOLS",
        {
            "run_tests": fake_run_tests,
            "edit_file": fake_edit_file,
        },
    ):
        agent = AgentLoop(
            llm=llm,
            max_iterations=5,
        )

        state = agent.run(
            task="Fix the failing test.",
            repository="demo-django",
        )

        print("STATUS:", state.status)
        print("FINAL:", state.final_message)
        print("ITERATIONS:", state.iteration)
        print("TOOL CALLS:", state.tool_calls)
        print("TEST RUNS:", state.test_runs)
        print("ERRORS:", state.errors)
        print("REPAIRS:", state.repair_history)

    assert state.status == "completed"

    assert state.repair_attempts == 1
    assert len(state.repair_history) == 1

    repair = state.repair_history[0]

    assert repair["attempt"] == 1
    assert repair["action"] == "edit_file"
    assert repair["file"] == "demo-django/app/views.py"
    assert repair["result"] == "success"

    assert len(state.edits) == 1

    edit = state.edits[0]

    assert edit["id"] == "edit-1"
    assert edit["success"] is True
    assert repair["edit_id"] == edit["id"]


def test_agent_loop_multi_repair_integration():
    class RepairLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            if self.calls == 2:
                return (
                    '{"action":"edit_file",'
                    '"arguments":{'
                    '"path":"demo-django/app/views.py",'
                    '"old_text":"return 500",'
                    '"new_text":"return 200"'
                    '}}'
                )

            if self.calls == 3:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            if self.calls == 4:
                return (
                    '{"action":"edit_file",'
                    '"arguments":{'
                    '"path":"demo-django/app/views.py",'
                    '"old_text":"return 200",'
                    '"new_text":"return 201"'
                    '}}'
                )

            if self.calls == 5:
                return (
                    '{"action":"run_tests",'
                    '"arguments":{"project_path":"demo-django"}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Repair completed."}}'
            )


    llm = RepairLLM()
    run_tests_calls = 0


    def fake_run_tests(project_path):
        nonlocal run_tests_calls

        run_tests_calls += 1

        if run_tests_calls <= 2:
            return {
                "success": False,
                "stderr": "AssertionError",
            }

        return {
            "success": True,
            "stdout": "1 passed",
        }

    def fake_edit_file(path, old_text, new_text):
        return {
            "success": True,
            "path": path,
        }

    with patch(
        "app.agent.loop.TOOLS",
        {
            "run_tests": fake_run_tests,
            "edit_file": fake_edit_file,
        },
    ):
        agent = AgentLoop(
            llm=llm,
            max_iterations=6,
        )

        state = agent.run(
            task="Fix the failing test.",
            repository="demo-django",
        )

        print("STATUS:", state.status)
        print("FINAL:", state.final_message)
        print("ITERATIONS:", state.iteration)
        print("TOOL CALLS:", state.tool_calls)
        print("TEST RUNS:", state.test_runs)
        print("ERRORS:", state.errors)
        print("REPAIRS:", state.repair_history)

    assert state.status == "completed"

    assert state.repair_attempts == 2
    assert len(state.edits) == 2
    assert len(state.repair_history) == 2

    assert state.repair_history[0]["result"] == "failed"
    assert state.repair_history[1]["result"] == "success"


def test_agent_loop_records_edit():
    class EditLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"edit_file",'
                    '"arguments":{'
                    '"path":"demo-django/app/views.py",'
                    '"old_text":"return 500",'
                    '"new_text":"return 200"'
                    '}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Edit completed."}}'
            )

    def fake_edit_file(path, old_text, new_text):
        return {
            "success": True,
            "path": path,
            "message": "File edited successfully.",
        }

    with patch(
        "app.agent.loop.TOOLS",
        {
            "edit_file": fake_edit_file,
        },
    ):
        agent = AgentLoop(llm=EditLLM(), max_iterations=3)

        state = agent.run(
            task="Change the response code.",
            repository="demo-django",
        )

    assert state.status == "completed"
    assert len(state.edits) == 1

    edit = state.edits[0]

    assert edit["id"] == "edit-1"
    assert edit["path"] == "demo-django/app/views.py"
    assert edit["old_text"] == "return 500"
    assert edit["new_text"] == "return 200"
    assert edit["success"] is True
    assert edit["error"] is None

def test_agent_loop_records_failed_edit():
    class EditLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, messages, **kwargs):
            self.calls += 1

            if self.calls == 1:
                return (
                    '{"action":"edit_file",'
                    '"arguments":{'
                    '"path":"demo-django/app/views.py",'
                    '"old_text":"does not exist",'
                    '"new_text":"return 200"'
                    '}}'
                )

            return (
                '{"action":"final",'
                '"arguments":{"message":"Edit attempted."}}'
            )

    def fake_edit_file(path, old_text, new_text):
        return {
            "success": False,
            "path": path,
            "error": "Target text was not found.",
        }

    with patch(
        "app.agent.loop.TOOLS",
        {
            "edit_file": fake_edit_file,
        },
    ):
        agent = AgentLoop(llm=EditLLM(), max_iterations=3)

        state = agent.run(
            task="Change the response code.",
            repository="demo-django",
        )

    assert state.status == "completed"
    assert len(state.edits) == 1

    edit = state.edits[0]

    assert edit["id"] == "edit-1"
    assert edit["success"] is False
    assert edit["error"] == "Target text was not found."


def test_agent_loop_fake_llm():

    class FakeLLM:
        def __init__(self):
            self.messages = None

        def generate(self, messages, **kwargs):
            self.messages = messages

            return (
                '{"action": "final", '
                '{"message": "done"}}'
        )
    fake_llm = FakeLLM()
    context_engine = Mock()

    context_engine.get_context.return_value = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 3,
            "source": "lexical",
            "content": "urlpatterns = []",
        }
    ]

    context_serializer = Mock()

    context_serializer.serialize.return_value = (
        "### File: demo-django/demo_django/urls.py\n"
        "```python\n"
        "urlpatterns = []\n"
        "```"
    )

    agent = AgentLoop(
    llm=fake_llm,
    context_engine=context_engine,
    context_serializer=context_serializer,
    )

    state = agent.run(
    "Find the URL configuration",
    "demo-django",
)
    context_engine.get_context.assert_called_once_with(
    "Find the URL configuration",
    "demo-django",
)
    context_serializer.serialize.assert_called_once_with(
    context_engine.get_context.return_value,
)
    user_message = fake_llm.messages[1]

    assert user_message["role"] == "user"
    assert "Find the URL configuration" in user_message["content"]
    assert "demo-django/demo_django/urls.py" in user_message["content"]
    assert "urlpatterns = []" in user_message["content"]