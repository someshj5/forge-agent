from app.skills.registry import SkillRegistry


class SkillRetriever:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def retrieve(
        self,
        task: str,
        limit: int = 3,
    ):
        if not task.strip():
            return []

        return self.registry.search(
            task,
            limit=limit,
        )