
from pathlib import Path

from app.skills.registry import SkillRegistry
from app.skills.retriever import SkillRetriever


SKILLS_ROOT = Path("/Users/someshjaiswal/.agent/skills/skills")


def make_retriever() -> SkillRetriever:
    registry = SkillRegistry(
        skills_root=SKILLS_ROOT
    )
    registry.load()

    return SkillRetriever(registry)


def test_retriever_finds_django_pro():
    retriever = make_retriever()

    results = retriever.retrieve(
        "Django development and ORM optimization",
        limit=5,
    )

    names = {
        result.skill.name
        for result in results
    }

    assert "django-pro" in names


def test_retriever_returns_scores():
    retriever = make_retriever()

    results = retriever.retrieve(
        "Django ORM optimization",
        limit=5,
    )

    django_result = next(
        result
        for result in results
        if result.skill.name == "django-pro"
    )

    assert django_result.score > 0


def test_retriever_respects_limit():
    retriever = make_retriever()

    results = retriever.retrieve(
        "Django Python API architecture",
        limit=2,
    )

    assert len(results) <= 2


def test_retriever_returns_empty_for_empty_task():
    retriever = make_retriever()

    results = retriever.retrieve("")

    assert results == []

