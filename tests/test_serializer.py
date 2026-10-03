from app.context.serializer import ContextSerializer


def test_serialize_empty_context():
    serializer = ContextSerializer()

    result = serializer.serialize([])

    assert result == ""


def test_serialize_single_file():
    serializer = ContextSerializer()

    context = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 3,
            "source": "lexical",
            "content": "urlpatterns = []",
        }
    ]

    result = serializer.serialize(context)

    assert "### File: demo-django/demo_django/urls.py" in result
    assert "urlpatterns = []" in result
    assert "```python" in result
    assert "```" in result

    assert "score" not in result
    assert "lexical" not in result


def test_serialize_multiple_files():
    serializer = ContextSerializer()

    context = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 3,
            "source": "lexical",
            "content": "urlpatterns = []",
        },
        {
            "path": "demo-django/app/views.py",
            "score": 2,
            "source": "lexical",
            "content": "class UserViewSet: pass",
        },
    ]

    result = serializer.serialize(context)

    assert "### File: demo-django/demo_django/urls.py" in result
    assert "urlpatterns = []" in result

    assert "### File: demo-django/app/views.py" in result
    assert "class UserViewSet: pass" in result

    assert result.index("urls.py") < result.index("views.py")