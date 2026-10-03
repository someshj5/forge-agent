from app.context.chunking import PythonChunker


def test_chunk_two_top_level_assignments():
    source = """\
INSTALLED_APPS = [
    "django.contrib.admin",
]

DATABASES = {
    "default": {}
}
"""

    chunker = PythonChunker()

    chunks = chunker.chunk(
        "demo-django/demo_django/settings.py",
        source,
    )

    assert len(chunks) == 2

    assert chunks[0]["path"] == (
        "demo-django/demo_django/settings.py"
    )

    assert chunks[0]["content"] == """\
INSTALLED_APPS = [
    "django.contrib.admin",
]
"""

    assert chunks[1]["content"] == """\
DATABASES = {
    "default": {}
}
"""

def test_chunk_function():
    source = """\
def calculate_total(a, b):
    result = a + b
    return result
"""

    chunker = PythonChunker()

    chunks = chunker.chunk(
        "example.py",
        source,
    )

    assert len(chunks) == 1
    assert chunks[0]["content"] == source
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 3

def test_empty_source_returns_empty_list():
    chunker = PythonChunker()

    chunks = chunker.chunk(
        "example.py",
        "",
    )

    assert chunks == []

def test_invalid_python_falls_back_to_whole_file():
    source = """\
def broken(
    return 10
"""

    chunker = PythonChunker()

    chunks = chunker.chunk(
        "example.py",
        source,
    )

    assert len(chunks) == 1
    assert chunks[0]["path"] == "example.py"
    assert chunks[0]["content"] == source
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 2