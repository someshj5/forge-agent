from pathlib import Path

from app.skills.registry import SkillRegistry


SKILLS_ROOT = Path("/Users/someshjaiswal/.agent/skills/skills")


def test_registry_loads_skills():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)

    count = registry.load()

    assert count > 800


def test_registry_get_django_pro():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)
    registry.load()

    skill = registry.get("django-pro")

    assert skill is not None
    assert skill.name == "django-pro"
    assert "Django 5.x" in skill.description


def test_registry_preserves_skill_path():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)
    registry.load()

    skill = registry.get("django-pro")

    assert skill is not None
    assert skill.path == SKILLS_ROOT / "django-pro" / "SKILL.md"


def test_registry_reads_model_metadata():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)
    registry.load()

    skill = registry.get("django-pro")

    assert skill is not None
    assert skill.model == "opus"


def test_registry_search_finds_django_skill():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)
    registry.load()

    results = registry.search(
        "Django ORM optimization",
        limit=5,
    )

    names = {
        result.skill.name
        for result in results
    }

    assert "django-pro" in names


def test_registry_search_returns_score():
    registry = SkillRegistry(skills_root=SKILLS_ROOT)
    registry.load()

    results = registry.search(
        "Django ORM optimization",
        limit=5,
    )

    django_result = next(
        result
        for result in results
        if result.skill.name == "django-pro"
    )

    assert django_result.score > 0