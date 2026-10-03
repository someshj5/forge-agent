from app.tools.web_search import (
    WebSearchResult,
    WebSearchTool,
    WebSearchProvider,
)


class FakeWebSearchProvider(WebSearchProvider):
    def search(self, query, max_results=5):
        return [
            WebSearchResult(
                title="Django Authentication",
                url="https://example.com/django-auth",
                snippet="Django authentication documentation.",
            ),
            WebSearchResult(
                title="Django Security",
                url="https://example.com/django-security",
                snippet="Django security documentation.",
            ),
        ][:max_results]


def test_web_search_returns_structured_results():
    provider = FakeWebSearchProvider()
    tool = WebSearchTool(provider)

    result = tool.search(
        query="Django authentication",
        max_results=2,
    )

    assert result["success"] is True
    assert result["query"] == "Django authentication"

    assert len(result["results"]) == 2

    assert result["results"][0] == {
        "title": "Django Authentication",
        "url": "https://example.com/django-auth",
        "snippet": "Django authentication documentation.",
    }


def test_web_search_rejects_empty_query():
    provider = FakeWebSearchProvider()
    tool = WebSearchTool(provider)

    result = tool.search("")

    assert result["success"] is False
    assert result["results"] == []
    assert result["error"] == "Query cannot be empty"


class FailingProvider(WebSearchProvider):
    def search(self, query, max_results=5):
        raise RuntimeError("Provider unavailable")


def test_web_search_handles_provider_failure():
    provider = FailingProvider()
    tool = WebSearchTool(provider)

    result = tool.search("Django authentication")

    assert result["success"] is False
    assert result["results"] == []
    assert result["error"] == "Provider unavailable"