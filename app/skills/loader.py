from pathlib import Path
from typing import Any

import yaml

from app.skills.models import SkillMetadata


class SkillLoader:
    def load_metadata(self, skill_path: Path) -> SkillMetadata:
        if not skill_path.exists():
            raise FileNotFoundError(
                f"Skill file not found: {skill_path}"
            )

        content = skill_path.read_text(
            encoding="utf-8"
        )

        frontmatter = self._parse_frontmatter(content)

        name = frontmatter.get("name")

        if not name:
            raise ValueError(
                f"Skill is missing 'name': {skill_path}"
            )

        description = frontmatter.get(
            "description",
            "",
        )

        allowed_tools = frontmatter.get(
            "allowed-tools",
            [],
        )

        if isinstance(allowed_tools, str):
            allowed_tools = [
                item.strip()
                for item in allowed_tools.split(",")
                if item.strip()
            ]

        metadata = frontmatter.get(
            "metadata",
            {},
        )

        model = None

        if isinstance(metadata, dict):
            model = metadata.get("model")

        return SkillMetadata(
            name=str(name),
            description=str(description),
            path=skill_path,
            allowed_tools=tuple(
                str(tool)
                for tool in allowed_tools
            ),
            model=str(model) if model else None,
        )

    def load_content(self, skill: SkillMetadata) -> str:
        return skill.path.read_text(
            encoding="utf-8"
        )

    def _parse_frontmatter(
        self,
        content: str,
    ) -> dict[str, Any]:

        if not content.startswith("---"):
            return {}

        parts = content.split(
            "---",
            2,
        )

        if len(parts) < 3:
            return {}

        frontmatter_text = parts[1]

        data = yaml.safe_load(
            frontmatter_text
        )

        if not isinstance(data, dict):
            return {}

        return data