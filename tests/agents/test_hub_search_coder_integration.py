
from unittest.mock import Mock

from app.agent.state import AgentState
from app.agents.coder_agent import CoderAgent
from app.agents.hub import HubAgent
from app.agents.search_agent import SearchAgent


def build_state():
    return AgentState(
        task="Change demo to production",
        repository="demo-django",
    )

def test_hub_routes_search_then_coder(monkeypatch):
    from unittest.mock import Mock

    from app.agents.base import AgentResult
    from app.agents.coder_agent import CoderAgent
    from app.agents.hub import HubAgent
    from app.agents.search_agent import SearchAgent
    from app.agent.state import AgentState

    state = AgentState(
        task="Add the comment '# Django URL routes' immediately above urlpatterns.",
        repository="demo-django",
    )

    # ---------------------------------------------------------
    # SearchAgent
    # ---------------------------------------------------------

    search_agent = SearchAgent()

    # Keep this integration test deterministic.
    monkeypatch.setattr(
        search_agent.context_engine,
        "get_context",
        lambda query, path: [
            {
                "path": "demo-django/demo_django/urls.py",
                "score": 5,
                "source": "lexical",
                "content": (
                    "from django.urls import path\n"
                    "\n"
                    "urlpatterns = [\n"
                    "    path('admin/', admin.site.urls),\n"
                    "]\n"
                ),
            }
        ],
    )

    # ---------------------------------------------------------
    # CoderAgent
    # ---------------------------------------------------------

    mock_llm = Mock()

    mock_llm.generate.return_value = """
    {
        "operation": "insert_before",
        "text": "# Django URL routes\\n"
    }
    """

    # Mock the EditEngine rather than app.agents.coder_agent.edit_file.
    mock_edit_engine = Mock()

    mock_edit_engine.apply.return_value = {
        "success": True,
    }

    coder_agent = CoderAgent(
        llm=mock_llm,
        edit_engine=mock_edit_engine,
    )

    # CoderAgent reads the file before generating the edit.
    monkeypatch.setattr(
        "app.agents.coder_agent.read_file",
        lambda path: {
            "success": True,
            "content": (
                "from django.urls import path\n"
                "\n"
                "urlpatterns = [\n"
                "    path('admin/', admin.site.urls),\n"
                "]\n"
            ),
        },
    )

    # ---------------------------------------------------------
    # Hub
    # ---------------------------------------------------------

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": coder_agent,
        }
    )

    # ---------------------------------------------------------
    # Step 1: Hub → SearchAgent
    # ---------------------------------------------------------

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "search"

    assert state.current_agent == "search"
    assert state.target_symbol == "urlpatterns"

    assert state.relevant_files == [
        "demo-django/demo_django/urls.py"
    ]

    # ---------------------------------------------------------
    # Step 2: Hub → CoderAgent
    # ---------------------------------------------------------

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "code"

    assert state.current_agent == "coder"

    # ---------------------------------------------------------
    # Verify EditEngine received the semantic operation
    # ---------------------------------------------------------

    mock_edit_engine.apply.assert_called_once()

    operation = mock_edit_engine.apply.call_args.kwargs[
        "operation"
    ]

    target_text = mock_edit_engine.apply.call_args.kwargs[
        "target_text"
    ]

    assert operation.path == (
    "demo-django/demo_django/urls.py"
    )

    assert operation.target_id.startswith("A")

    assert operation.operation.value == (
        "insert_before"
    )

    assert operation.text == (
        "# Django URL routes\n"
    )

    assert target_text == "urlpatterns = ["

def test_hub_does_not_route_to_coder_before_search():
    state = build_state()

    search_agent = Mock()
    search_agent.run.return_value = Mock(
        success=True,
        error=None,
    )

    code_agent = Mock()

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": code_agent,
        }
    )

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "search"

    search_agent.run.assert_called_once_with(state)
    code_agent.run.assert_not_called()


def test_hub_routes_to_coder_after_search():
    state = build_state()

    state.relevant_files = [
        "demo-django/demo_django/settings.py"
    ]

    search_agent = Mock()

    code_agent = Mock()
    code_agent.run.return_value = Mock(
        success=True,
        error=None,
    )

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": code_agent,
        }
    )

    result = hub.run(state)

    assert result.success is True
    assert result.data["next_agent"] == "code"

    search_agent.run.assert_not_called()
    code_agent.run.assert_called_once_with(state)

