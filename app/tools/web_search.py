from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class WebSearchResult:
    title: str
    url: str
    snippet: str


class WebSearchProvider(ABC):

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[WebSearchResult]:
        raise NotImplementedError


class WebSearchTool:
    def __init__(self, provider: WebSearchProvider):
        self.provider = provider

    def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> dict:
        if not query.strip():
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": "Query cannot be empty",
            }

        try:
            results = self.provider.search(
                query=query,
                max_results=max_results,
            )

            return {
                "success": True,
                "query": query,
                "results": [
                    {
                        "title": result.title,
                        "url": result.url,
                        "snippet": result.snippet,
                    }
                    for result in results
                ],
            }

        except Exception as exc:
            return {
                "success": False,
                "query": query,
                "results": [],
                "error": str(exc),
            }