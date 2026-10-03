from app.tools.search import search_code


def test_search_code():

    result = search_code(
        "urlpatterns",
        "demo-django",
    )

    assert result["success"] is True
    assert result["match_count"] > 0


def test_search_path_traversal():

    result = search_code(
        "urlpatterns",
        "../../",
    )

    assert result["success"] is False


def test_search_no_match():

    result = search_code(
        "THIS_SHOULD_NOT_EXIST_123456",
        "demo-django",
    )

    assert result["success"] is True
    assert result["matches"] == []