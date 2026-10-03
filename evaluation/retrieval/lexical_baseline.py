from app.context.engine import ContextEngine
import pytest


def recall_at_k(retrieved, expected, k):
    if not expected:
        raise ValueError("Expected files cannot be empty")

    top_k = retrieved[:k]
    relevant_retrieved = set(top_k) & set(expected)
    return len(relevant_retrieved) / len(expected) if expected else 0.0


def evaluate_case(case: dict, k: int = 5) -> float:
    engine = ContextEngine()

    candidates = engine.retrieve(
        case["query"],
        "demo-django",
    )

    retrieved_paths = [
        candidate["path"]
        for candidate in candidates
    ]


    return recall_at_k(
        retrieved_paths,
        case["expected_files"],
        k,
    )

def evaluate_dataset(cases: list[dict], k: int = 5) -> dict:
    if not cases:
        raise ValueError("Evaluation cases cannot be empty")
    result=[]
    for case in cases:
        recall = evaluate_case(case)
        result.append({
            "task": case["task"],
            "recall": recall,
        })

    mean_recall = sum(
        item["recall"] for item in result
    ) / len(result)

    return {
        "mean_recall": mean_recall,
        "cases": result,
    }

