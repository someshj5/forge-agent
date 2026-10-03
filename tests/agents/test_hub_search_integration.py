from unittest.mock import Mock

from app.agents.base import AgentResult
from app.agents.hub import HubAgent
from app.agents.search_agent import SearchAgent
from app.agent.state import AgentState


def test_hub_delegates_to_search_and_updates_shared_state():
    state = AgentState(
        task="Find the Django URL configuration",
        repository="demo-django",
    )

    context_engine = Mock()

    context_engine.get_context.return_value = [
        {
            "path": "demo-django/demo_django/urls.py",
            "content": "urlpatterns = []",
        }
    ]

    search_agent = SearchAgent(
        context_engine=context_engine,
    )

    hub = HubAgent(
        agents={
            "search": search_agent,
        }
    )

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "search"

    assert state.current_agent == "search"

    assert state.relevant_files == [
        "demo-django/demo_django/urls.py"
    ]


def test_hub_routes_to_code_after_search():
    state = AgentState(
        task="Find the Django URL configuration",
        repository="demo-django",
        relevant_files=[
            "demo-django/demo_django/urls.py"
        ],
    )

    hub = HubAgent(
        agents={}
    )

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "code"
