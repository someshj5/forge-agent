
from unittest.mock import patch

from app.context.engine import ContextEngine
from unittest.mock import Mock


def test_context_engine():

    search_result = {
    "success": True,
    "matches": [
        "demo-django/demo_django/urls.py:10:urlpatterns"
    ],
    }

    ranked_result = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 1,
            "source": "lexical",
        }
    ]

    with patch(
    "app.context.engine.search_code",
    return_value=search_result,
    ) as search_mock, patch(
        "app.context.engine.rank_matches",
        return_value=ranked_result,
    ) as rank_mock:
        

        # Your code here
        engine = ContextEngine()
        result = engine.retrieve("urlpatterns","demo-django",)

    search_mock.assert_called_once_with(
        "urlpatterns",
        "demo-django",
    )

    rank_mock.assert_called_once_with(
        search_result,
    )
    assert result == ranked_result


def test_context_engine_uses_default_path():
    search_result = {
        "success": True,
        "matches": [],
    }

    ranked_result = []

    with patch(
        "app.context.engine.search_code",
        return_value=search_result,
    ) as search_mock, patch(
        "app.context.engine.rank_matches",
        return_value=ranked_result,
    ):

        engine = ContextEngine()

        result = engine.retrieve("urlpatterns")

    search_mock.assert_called_once_with(
        "urlpatterns",
        ".",
    )

    assert result == ranked_result

def test_context_engine_get_context():
    engine = ContextEngine()
    ranked_candidates = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 3,
            "source": "lexical",
        }   
    ]
    engine.retrieve = Mock(return_value=ranked_candidates)
    context = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 3,
            "source": "lexical",
            "content": "urlpatterns = [...]",
        }
    ]
    engine.builder.build = Mock(return_value=context)

    result = engine.get_context(
        "urlpatterns",
        "demo-django",
    )

    engine.retrieve.assert_called_once_with(
        "urlpatterns",
        "demo-django",
    )

    engine.builder.build.assert_called_once_with(
    ranked_candidates,
    )

    assert result == context