from unittest.mock import Mock, patch

# from evaluation.retrieval.cases import evaluate_case
from evaluation.retrieval.lexical_baseline import evaluate_dataset, recall_at_k
from evaluation.retrieval.lexical_baseline import evaluate_case
import pytest

def test_recall_at_k_perfect():
    retrieved = ["a.py", "b.py", "c.py"]
    expected = ["a.py", "b.py", "c.py"]

    result = recall_at_k(retrieved, expected, 3)

    assert result == 1.0

def test_recall_at_k_partial():
    retrieved = ["a.py", "x.py", "b.py"]
    expected = ["a.py", "b.py", "c.py"]

    result = recall_at_k(retrieved, expected, 3)

    assert result == 2 / 3

def test_recall_at_k_zero_hits():
    retrieved = ["x.py", "y.py"]
    expected = ["a.py", "b.py"]

    result = recall_at_k(retrieved, expected, 2)

    assert result == 0.0

def test_recall_at_k_empty_expected():
    retrieved = ["a.py"]

    try:
        recall_at_k(retrieved, [], 1)
    except ValueError as exc:
        assert str(exc) == "Expected files cannot be empty"
    else:
        assert False, "Expected ValueError"

def test_recall_at_k_empty_expected():
    with pytest.raises(ValueError, match="Expected files cannot be empty"):
        recall_at_k(["a.py"], [], 1)

def test_recall_at_k_respects_k():
    retrieved = ["a.py", "x.py", "b.py", "c.py"]
    expected = ["a.py", "b.py", "c.py"]

    result = recall_at_k(retrieved, expected, 2)

    assert result == 1 / 3


def test_evaluate_case():
    case = {
        "task": "Find the URL configuration",
        "query": "urlpatterns",
        "expected_files": [
            "demo-django/demo_django/urls.py",
        ],
    }

    fake_candidates = [
        {
            "path": "demo-django/demo_django/urls.py",
            "score": 2,
            "source": "lexical",
        }
    ]

    fake_engine = Mock()
    fake_engine.retrieve.return_value = fake_candidates

    with patch(
        "evaluation.retrieval.lexical_baseline.ContextEngine",
        return_value=fake_engine,
    ):
        result = evaluate_case(case, k=1)

    fake_engine.retrieve.assert_called_once_with(
        "urlpatterns",
        "demo-django",
    )

    assert result == 1.0

def test_evaluate_dataset():
    cases = [
        {"task": "case 1"},
        {"task": "case 2"},
        {"task": "case 3"},
    ]

    with patch(
        "evaluation.retrieval.lexical_baseline.evaluate_case",
        side_effect=[1.0, 0.5, 0.0],
    ) as mock_evaluate:
        result = evaluate_dataset(cases, k=3)

    assert result["mean_recall"] == 0.5
    assert result["cases"] == [
        {"task": "case 1", "recall": 1.0},
        {"task": "case 2", "recall": 0.5},
        {"task": "case 3", "recall": 0.0},
    ]

def test_evaluate_dataset_empty():
    with pytest.raises(
        ValueError,
        match="Evaluation cases cannot be empty",
    ):
        evaluate_dataset([])