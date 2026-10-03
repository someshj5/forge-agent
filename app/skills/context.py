from app.skills.models import SkillMetadata
from app.skills.registry import SkillRegistry


class SkillContextLoader:
    def __init__(self, registry: SkillRegistry):
        self.registry = registry

    def load(self, skill: SkillMetadata) -> dict:
        content = skill.path.read_text(
            encoding="utf-8"
        )

        return {
            "name": skill.name,
            "description": skill.description,
            "content": content,
        }

    def load_many(self, skills: list[SkillMetadata]) -> list[dict]:
        return [
            self.load(skill)
            for skill in skills
        ]