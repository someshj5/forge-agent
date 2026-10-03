from dataclasses import dataclass
from pathlib import Path
import re
import math
import yaml

from app.skills.loader import SkillLoader
from app.skills.models import SkillMetadata


@dataclass(frozen=True)
class SkillSearchResult:
    skill: SkillMetadata
    score: float


class SkillRegistry:
    def __init__(
        self,
        skills_root: str | Path,
        loader: SkillLoader | None = None,
    ):
        self.skills_root = Path(
            skills_root
        ).resolve()

        self.loader = (
            loader
            or SkillLoader()
        )

        self._skills: dict[
            str,
            SkillMetadata,
        ] = {}

        self._document_frequency: dict[str, int] = {}
        self._average_document_length = 0.0
        self._document_count = 0

        self._bm25_k1 = 1.5
        self._bm25_b = 0.75

    def load(self) -> int:
        self._skills.clear()

        skill_files = sorted(
            self.skills_root.rglob("SKILL.md")
        )

        for skill_path in skill_files:
            try:
                metadata = self.loader.load_metadata(
                    skill_path
                )
            except (
                OSError,
                ValueError,
                yaml.YAMLError,
            ):
                continue

            self._skills[metadata.name] = metadata

        self._build_statistics()

        return len(self._skills)

    def _build_statistics(self) -> None:
        self._document_frequency.clear()

        lengths = []

        for skill in self._skills.values():
            tokens = self._tokenize(
                f"{skill.name} {skill.description}"
            )

            lengths.append(len(tokens))

            for token in tokens:
                self._document_frequency[token] = (
                    self._document_frequency.get(token, 0)
                    + 1
                )

        if lengths:
            self._average_document_length = (
                sum(lengths) / len(lengths)
            )
        else:
            self._average_document_length = 0.0

    def get(
        self,
        name: str,
    ) -> SkillMetadata | None:
        return self._skills.get(name)

    def all(
        self,
    ) -> list[SkillMetadata]:
        return list(
            self._skills.values()
        )

    def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[SkillSearchResult]:

        if not query.strip():
            return []

        query_tokens = self._tokenize(
            query
        )

        scored = []

        for skill in self._skills.values():
            score = self._score(
                skill,
                query_tokens,
            )

            if score > 0:
                scored.append(
                    SkillSearchResult(
                        skill=skill,
                        score=score,
                    )
                )

        scored.sort(
            key=lambda item: (
                -item.score,
                item.skill.name,
            )
        )

        return scored[:limit]


    def _score(
        self,
        skill: SkillMetadata,
        query_tokens: set[str],
    ) -> float:
        document_text = f"{skill.name} {skill.description}"
        document_tokens = re.findall(
            r"[a-zA-Z0-9]+",
            document_text.lower(),
        )

        document_length = len(document_tokens)

        if document_length == 0:
            return 0.0

        score = 0.0

        for token in query_tokens:
            if token not in self._document_frequency:
                continue

            term_frequency = document_tokens.count(token)

            if term_frequency == 0:
                continue

            document_frequency = self._document_frequency[token]

            idf = math.log(
                (
                    (self._document_count - document_frequency + 0.5)
                    / (document_frequency + 0.5)
                )
                + 1
            )

            numerator = (
                term_frequency * (self._bm25_k1 + 1)
            )

            denominator = (
                term_frequency
                + self._bm25_k1
                * (
                    1
                    - self._bm25_b
                    + self._bm25_b
                    * (
                        document_length
                        / self._average_document_length
                    )
                )
            )

            score += idf * (numerator / denominator)

        # Small boost for matching skill names.
        name_tokens = self._tokenize(skill.name)
        name_overlap = len(query_tokens & name_tokens)
        score += name_overlap * 2.0

        return score

    @staticmethod
    def _tokenize(
        text: str,
    ) -> set[str]:

        return set(
            re.findall(
                r"[a-zA-Z0-9]+",
                text.lower(),
            )
        )