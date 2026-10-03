from app.context.lexical import rank_matches
from app.tools.search import search_code


# def test_lexical_multiple_match():
#     result = search_code(
#             "urlpatterns",
#             "demo-django",
#         )
#     scores = rank_matches(result)

#     assert scores != []
#     assert scores[0]["source"] == "lexical"
#     assert scores[0]["score"] >=1

from app.context.lexical import rank_matches


def test_lexical_multiple_match():
    result = {
        "success": True,
        "query": "urlpatterns",
        "matches": [
            "demo-django/demo_django/urls.py:10:urlpatterns = []",
            "demo-django/demo_django/urls.py:20:urlpatterns += routes",
            "demo-django/users/urls.py:5:urlpatterns = []",
        ],
    }

    scores = rank_matches(result)

    assert len(scores) == 2
    assert scores[0]["path"] == "demo-django/demo_django/urls.py"
    assert scores[0]["score"] == 2
    assert scores[1]["path"] == "demo-django/users/urls.py"
    assert scores[1]["score"] == 1
    assert scores[0]["source"] == "lexical"


def test_lexical_empty_matches():
    result = {
        "success": True,
        "matches": [],
    }

    assert rank_matches(result) == []


def test_lexical_failed_search():
    result = {
        "success": False,
        "error": "Search timed out.",
    }

    assert rank_matches(result) == []