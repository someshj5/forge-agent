
from pathlib import Path
from unittest.mock import Mock

from app.agent.state import AgentState
from app.agents.search_agent import SearchAgent
from app.skills.models import SkillMetadata
from app.skills.registry import SkillSearchResult


def test_search_agent_updates_relevant_files():
    context_engine = Mock()

    context_engine.get_context.return_value = [
        {
            "path": "demo-django/demo_django/settings.py",
            "content": "DATABASES = {}",
        },
        {
            "path": "demo-django/demo_django/urls.py",
            "content": "urlpatterns = []",
        },
    ]

    agent = SearchAgent(
        context_engine=context_engine,
    )

    state = AgentState(
        task="Find the database configuration",
        repository="demo-django",
    )

    result = agent.run(state)

    assert result.success is True
    assert result.agent == "search"

    assert state.relevant_files == [
        "demo-django/demo_django/settings.py",
        "demo-django/demo_django/urls.py",
    ]

    assert result.data["relevant_files"] == [
        "demo-django/demo_django/settings.py",
        "demo-django/demo_django/urls.py",
    ]

    context_engine.get_context.assert_called_once_with(
        "Find the database configuration",
        "demo-django",
    )


def test_search_agent_uses_web_search_for_documentation_task():
    context_engine = Mock()

    context_engine.get_context.return_value = []

    web_search_tool = Mock()

    web_search_tool.search.return_value = {
        "success": True,
        "query": "Find the latest Django authentication documentation",
        "results": [
            {
                "title": "Django Authentication",
                "url": "https://example.com",
                "snippet": "Authentication documentation",
            }
        ],
    }

    agent = SearchAgent(
        context_engine=context_engine,
        web_search_tool=web_search_tool,
    )

    state = AgentState(
        task="Find the latest Django authentication documentation",
        repository="demo-django",
    )

    result = agent.run(state)

    assert result.success is True

    web_search_tool.search.assert_called_once_with(
        "Find the latest Django authentication documentation"
    )

    assert len(result.data["web_results"]) == 1

    assert result.data["web_results"][0] == {
        "title": "Django Authentication",
        "url": "https://example.com",
        "snippet": "Authentication documentation",
    }

    assert state.web_results == result.data["web_results"]


def test_search_agent_does_not_use_web_for_repository_task():
    context_engine = Mock()

    context_engine.get_context.return_value = [
        {
            "path": "demo-django/demo_django/settings.py",
            "content": "DATABASES = {}",
        }
    ]

    web_search_tool = Mock()

    agent = SearchAgent(
        context_engine=context_engine,
        web_search_tool=web_search_tool,
    )

    state = AgentState(
        task="Find the database configuration",
        repository="demo-django",
    )

    result = agent.run(state)

    assert result.success is True

    assert result.data["web_results"] == []
    assert state.web_results == []

    web_search_tool.search.assert_not_called()


def test_search_agent_retrieves_skill():
    context_engine = Mock()

    context_engine.get_context.return_value = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 5,
            "matches": [
                "urlpatterns = [",
            ],
            "content": (
                "urlpatterns = [\n"
                "    path('admin/', admin.site.urls),\n"
                "]\n"
            ),
        }
    ]

    skill_retriever = Mock()

    django_skill = SkillMetadata(
        name="django-pro",
        description="Django development and ORM optimization",
        path=Path("/tmp/django-pro/SKILL.md"),
    )

    skill_retriever.retrieve.return_value = [
        SkillSearchResult(
            skill=django_skill,
            score=10,
        )
    ]

    skill_context_loader = Mock()

    skill_context_loader.load_many.return_value = [
        {
            "name": "django-pro",
            "description": django_skill.description,
            "content": "Django skill content",
        }
    ]

    agent = SearchAgent(
        context_engine=context_engine,
        skill_retriever=skill_retriever,
        skill_context_loader=skill_context_loader,
    )

    state = AgentState(
        task="Add a comment above urlpatterns",
        repository="demo-django",
    )

    result = agent.run(state)

    assert result.success is True

    assert result.agent == "search"

    assert state.relevant_files == [
        "demo-django/demo_django/urls.py",
    ]

    assert state.target_symbol == "urlpatterns"

    assert state.selected_skills == [
        "django-pro",
    ]

    assert state.skill_context == [
        {
            "name": "django-pro",
            "description": django_skill.description,
            "content": "Django skill content",
        }
    ]

    assert result.data["selected_skills"] == [
        "django-pro",
    ]

    assert result.data["skill_context"] == [
        {
            "name": "django-pro",
            "description": django_skill.description,
            "content": "Django skill content",
        }
    ]

    skill_retriever.retrieve.assert_called_once()

    skill_query = (
        skill_retriever.retrieve.call_args.args[0]
    )

    assert "Add a comment above urlpatterns" in skill_query
    assert "demo-django" in skill_query
    assert "urlpatterns" in skill_query
    assert "demo-django/demo_django/urls.py" in skill_query
    assert "Django" in skill_query
    assert "Python" in skill_query
    assert "URL routing" in skill_query

    skill_retriever.retrieve.assert_called_once_with(
        skill_query,
        limit=3,
    )

    skill_context_loader.load_many.assert_called_once_with(
        [django_skill],
    )

