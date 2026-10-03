from unittest.mock import Mock
import pytest
from app.context.semantic import SemanticRetriever


def test_embed_documents():
    retriever = SemanticRetriever.__new__(SemanticRetriever)
    retriever.model = Mock()

    retriever.model.encode.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]

    documents = [
        {"path": "a.py", "content": "hello"},
        {"path": "b.py", "content": "world"},
    ]

    result = retriever._embed_documents(documents)

    retriever.model.encode.assert_called_once_with(
    ["hello", "world"],
    normalize_embeddings=True,
)
    assert result[0]["embedding"] == [0.1, 0.2]
    assert result[1]["embedding"] == [0.3, 0.4]

    assert result[0]["path"] == "a.py"
    assert result[0]["content"] == "hello"

    assert result[1]["path"] == "b.py"
    assert result[1]["content"] == "world"

def test_embed_documents_empty():
    retriever = SemanticRetriever.__new__(SemanticRetriever)
    retriever.model = Mock()

    result = retriever._embed_documents([])

    assert result == []
    retriever.model.encode.assert_not_called()


def test_embed_query():
    retriever = SemanticRetriever.__new__(SemanticRetriever)
    retriever.model = Mock()

    retriever.model.encode.return_value = [0.1, 0.2]

    result = retriever._embed_query("database setup")

    retriever.model.encode.assert_called_once_with(
        "database setup",
        normalize_embeddings=True,
    )

    assert result == [0.1, 0.2]

def test_embed_query_empty():
    retriever = SemanticRetriever.__new__(SemanticRetriever)
    retriever.model = Mock()

    with pytest.raises(ValueError, match="Query cannot be empty"):
        retriever._embed_query("")

    retriever.model.encode.assert_not_called()


def test_rank_documents():
    retriever = SemanticRetriever.__new__(SemanticRetriever)

    documents = [
        {
            "path": "a.py",
            "embedding": [1.0, 0.0],
        },
        {
            "path": "b.py",
            "embedding": [0.0, 1.0],
        },
        {
            "path": "c.py",
            "embedding": [0.8, 0.6],
        },
    ]

    query_embedding = [1.0, 0.0]

    result = retriever._rank_documents(
        documents,
        query_embedding,
        top_k=2,
    )

    assert result[0]["path"] == "a.py"
    assert result[0]["score"] == 1.0

    assert result[1]["path"] == "c.py"
    assert result[1]["score"] == 0.8

    assert len(result) == 2


from unittest.mock import Mock

from app.context.semantic import SemanticRetriever

from unittest.mock import Mock

from app.context.semantic import SemanticRetriever


def test_search_orchestrates_retrieval_pipeline():
    retriever = SemanticRetriever.__new__(SemanticRetriever)

    retriever._get_files = Mock()
    retriever._load_documents = Mock()
    retriever._embed_documents = Mock()
    retriever._embed_query = Mock()
    retriever._rank_documents = Mock()

    files = [
        "demo-django/settings.py",
        "demo-django/urls.py",
    ]

    documents = [
        {
            "path": "demo-django/settings.py",
            "content": "DATABASES = {}",
        },
        {
            "path": "demo-django/urls.py",
            "content": "urlpatterns = []",
        },
    ]

    embedded_documents = [
        {
            "path": "demo-django/settings.py",
            "content": "DATABASES = {}",
            "embedding": [1.0, 0.0],
        },
        {
            "path": "demo-django/urls.py",
            "content": "urlpatterns = []",
            "embedding": [0.0, 1.0],
        },
    ]

    query_embedding = [1.0, 0.0]

    ranked_results = [
        {
            "path": "demo-django/settings.py",
            "score": 1.0,
            "source": "semantic",
        }
    ]

    retriever._get_files.return_value = files
    retriever._load_documents.return_value = documents
    retriever._embed_documents.return_value = embedded_documents
    retriever._embed_query.return_value = query_embedding
    retriever._rank_documents.return_value = ranked_results

    result = retriever.search(
        query="database setup",
        path="demo-django",
        top_k=3,
    )

    assert result == ranked_results

    retriever._get_files.assert_called_once_with("demo-django")
    retriever._load_documents.assert_called_once_with(files)
    retriever._embed_documents.assert_called_once_with(documents)
    retriever._embed_query.assert_called_once_with("database setup")
    retriever._rank_documents.assert_called_once_with(
        embedded_documents,
        query_embedding,
        2,
    )

def test_search_returns_empty_when_no_files_found():
    retriever = SemanticRetriever.__new__(SemanticRetriever)

    retriever._get_files = Mock(return_value=[])

    retriever._load_documents = Mock()
    retriever._embed_documents = Mock()
    retriever._embed_query = Mock()
    retriever._rank_documents = Mock()

    result = retriever.search(
        query="database setup",
        path="demo-django",
    )

    assert result == []

    retriever._get_files.assert_called_once_with("demo-django")

    retriever._load_documents.assert_not_called()
    retriever._embed_documents.assert_not_called()
    retriever._embed_query.assert_not_called()
    retriever._rank_documents.assert_not_called()


def test_load_documents_returns_chunks():
    chunker = Mock()

    retriever = SemanticRetriever.__new__(SemanticRetriever)

    retriever.chunker = chunker

    source = {
        "success": True,
        "content": "DATABASES = {}",
    }

    chunk = {
        "path": "demo-django/settings.py",
        "chunk_id": "demo-django/settings.py:1-1",
        "content": "DATABASES = {}",
        "start_line": 1,
        "end_line": 1,
    }

    chunker.chunk.return_value = [chunk]

    # You'll need to patch read_file in the module
    # rather than calling the real filesystem.

def test_deduplicate_by_path():
    retriever = SemanticRetriever.__new__(SemanticRetriever)

    results = [
        {
            "path": "settings.py",
            "chunk_id": "settings.py:1-5",
            "score": 0.95,
        },
        {
            "path": "settings.py",
            "chunk_id": "settings.py:10-15",
            "score": 0.90,
        },
        {
            "path": "urls.py",
            "chunk_id": "urls.py:1-5",
            "score": 0.80,
        },
    ]

    result = retriever._deduplicate_by_path(
        results,
        top_k=2,
    )

    assert len(result) == 2
    assert result[0]["path"] == "settings.py"
    assert result[1]["path"] == "urls.py"