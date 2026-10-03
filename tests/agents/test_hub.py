from app.agents.hub import HubAgent
from app.agent.state import AgentState
from unittest.mock import Mock
from app.agents.base import AgentResult

def test_hub_starts_with_search():
    state = AgentState(
        task="Find the database configuration",
        repository="demo-django",
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.success is True
    assert result.agent == "hub"
    assert result.data["next_agent"] == "search"
    assert state.next_agent == "search"


def test_hub_moves_to_code_after_search():
    state = AgentState(
        task="Find the database configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/settings.py"
        ],
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.data["next_agent"] == "code"

def test_hub_moves_to_test_after_edit():
    state = AgentState(
        task="Change the database configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/settings.py"
        ],
        edits=[
            {
                "id": "edit-1",
                "path": "demo-django/demo_django/settings.py",
            }
        ],
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.data["next_agent"] == "test"


def test_hub_finishes_after_successful_tests():
    state = AgentState(
        task="Change the database configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/settings.py"
        ],
        edits=[
            {
                "id": "edit-1",
                "path": "demo-django/demo_django/settings.py",
            }
        ],
        test_runs=[
            {
                "success": True,
                "status": "passed",
            }
        ],
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.data["next_agent"] == "final"

def test_hub_routes_failed_tests_to_repair():
    state = AgentState(
        task="Change the database configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/settings.py"
        ],
        edits=[
            {
                "id": "edit-1",
                "path": "demo-django/demo_django/settings.py",
            }
        ],
        test_runs=[
            {
                "success": False,
                "status": "failed",
            }
        ],
        repair_attempts=0,
        max_repair_attempts=3,
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.data["next_agent"] == "repair"


def test_hub_fails_after_repair_budget_exhausted():
    state = AgentState(
        task="Change the database configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/settings.py"
        ],
        edits=[
            {
                "id": "edit-1",
                "path": "demo-django/demo_django/settings.py",
            }
        ],
        test_runs=[
            {
                "success": False,
                "status": "failed",
            }
        ],
        repair_attempts=3,
        max_repair_attempts=3,
    )

    hub = HubAgent()

    result = hub.run(state)

    assert result.data["next_agent"] == "failed"

def test_hub_delegates_to_search_agent():
    search_agent = Mock()

    search_agent.run.return_value = AgentResult(
        success=True,
        agent="search",
        data={
            "files": [
                "demo-django/demo_django/settings.py"
            ]
        },
    )

    hub = HubAgent(
        agents={
            "search": search_agent,
        }
    )

    state = AgentState(
        task="Find the database configuration",
        repository="demo-django",
    )

    result = hub.run(state)

    search_agent.run.assert_called_once_with(state)

    assert result.success is True
    assert result.data["next_agent"] == "search"
    assert result.data["agent_result"].agent == "search"

