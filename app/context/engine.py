from app.context.builder import ContextBuilder
from app.context.lexical import rank_matches
from app.tools.search import search_code


class ContextEngine:
    def __init__(self, builder=None):
        self.builder = builder or ContextBuilder()

    def retrieve(self, query: str, path: str = ".") -> list[dict]:
        result = search_code(query, path)
        scores = rank_matches(result)
        return scores

    def get_context(self, query: str, path: str = ".") -> list[dict]:
        candidates = self.retrieve(query, path)
        return self.builder.build(candidates)