
from app.context.builder import ContextBuilder
from unittest.mock import patch


def test_context_builder_empty_candidates():
    builder = ContextBuilder()

    result = builder.build([])

    assert result == []
    
def test_context_builder():
    candidates = [
            {
                "path": "demo-django/demo_django/urls.py",
                "score": 1,
                "source": "lexical",
            }
        ]
    builder = ContextBuilder()
    result = builder.build(candidates)

    assert result[0]['content'] != ""
    assert result[0]['score'] == 1
    assert result[0]['path'] == "demo-django/demo_django/urls.py"
    assert result[0]['source'] == "lexical"
    assert "error" not in result[0]




def test_context_builder_read_failure():
    candidates = [
        {
            "path": "demo-django/missing.py",
            "score": 1,
            "source": "lexical",
        }
    ]

    failed_result = {
        "success": False,
        "error": "File not found",
    }

    with patch(
        "app.context.builder.read_file",
        return_value=failed_result,
    ):

        builder = ContextBuilder()
        result = builder.build(candidates)

    assert len(result) == 1
    assert result[0]["path"] == "demo-django/missing.py"
    assert result[0]["error"] == "File not found"
    
