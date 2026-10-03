from unittest.mock import Mock

from app.agent.state import AgentState
from app.agents.base import AgentResult
from app.agents.hub import HubAgent
from app.agents.orchestrator import AgentOrchestrator


def test_orchestrator_runs_until_final():
    state = AgentState(
        task="Add a comment",
        repository="demo-django",
    )

    # ---------------------------------------------------------
    # SearchAgent
    # ---------------------------------------------------------

    search_agent = Mock()

    def search_run(state):
        # This is the important part.
        # SearchAgent changes shared state.
        state.relevant_files = [
            "demo-django/demo_django/urls.py"
        ]

        state.target_symbol = "urlpatterns"

        return AgentResult(
            success=True,
            agent="search",
            data={
                "relevant_files": state.relevant_files,
                "target_symbol": state.target_symbol,
            },
        )

    search_agent.run.side_effect = search_run

    # ---------------------------------------------------------
    # CoderAgent
    # ---------------------------------------------------------

    code_agent = Mock()

    def code_run(state):
        # CoderAgent changes shared state.
        state.edits.append(
            {
                "id": "edit-1",
                "success": True,
            }
        )

        return AgentResult(
            success=True,
            agent="coder",
        )

    code_agent.run.side_effect = code_run

    # ---------------------------------------------------------
    # TesterAgent
    # ---------------------------------------------------------

    test_agent = Mock()

    def test_run(state):
        # TesterAgent changes shared state.
        state.test_runs.append(
            {
                "success": True,
            }
        )

        return AgentResult(
            success=True,
            agent="tester",
        )

    test_agent.run.side_effect = test_run

    # ---------------------------------------------------------
    # Hub
    # ---------------------------------------------------------

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": code_agent,
            "test": test_agent,
        }
    )

    # ---------------------------------------------------------
    # Orchestrator
    # ---------------------------------------------------------

    orchestrator = AgentOrchestrator(hub)

    result = orchestrator.run(state)

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert result.status == "completed"

    search_agent.run.assert_called_once_with(state)
    code_agent.run.assert_called_once_with(state)
    test_agent.run.assert_called_once_with(state)