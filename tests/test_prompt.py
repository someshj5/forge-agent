from app.context.prompt import PromptBuilder


def test_prompt_builder():
    builder = PromptBuilder()

    result = builder.build(
        "Add a health check endpoint",
        "### File: demo-django/urls.py\n```python\nurlpatterns = []\n```",
    )

    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
    assert "Add a health check endpoint" in result[1]["content"]
    assert "demo-django/urls.py" in result[1]["content"]


def test_prompt_builder_empty_context():
    builder = PromptBuilder()

    result = builder.build(
        "Add a health check endpoint",
        "",
    )

    assert len(result) == 2
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"

    assert "Add a health check endpoint" in result[1]["content"]
    assert "Repository Context:" in result[1]["content"]