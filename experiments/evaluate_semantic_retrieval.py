import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.context.semantic import SemanticRetriever
from evaluation.retrieval.cases import SEMANTIC_CASES


def recall_at_k(retrieved, expected, k):
    if not expected:
        raise ValueError("Expected files cannot be empty")

    top_k = retrieved[:k]

    relevant = set(top_k) & set(expected)

    return len(relevant) / len(expected)


def evaluate_case(retriever, case, k=5):
    results = retriever.search(
        query=case["query"],
        path="demo-django",
        top_k=k,
    )

    print("\nRetrieved:")
    for rank, result in enumerate(results, start=1):
        print(
            f"{rank}. "
            f"{result['path']} "
            f"score={result['score']:.4f}"
    )

    retrieved_paths = [
        result["path"]
        for result in results
    ]

    return recall_at_k(
        retrieved_paths,
        case["expected_files"],
        k,
    )


def evaluate_dataset(cases, retriever, k=5):
    if not cases:
        raise ValueError("Evaluation cases cannot be empty")

    results = []

    for case in cases:
        recall = evaluate_case(
            retriever,
            case,
            k,
        )

        results.append({
            "task": case["task"],
            "query": case["query"],
            "recall": recall,
        })

    mean_recall = (
        sum(item["recall"] for item in results)
        / len(results)
    )

    return {
        "mean_recall": mean_recall,
        "cases": results,
    }


def main():
    retriever = SemanticRetriever()

    result = evaluate_dataset(
        SEMANTIC_CASES,
        retriever,
        k=5,
    )

    print("=" * 60)
    print("SEMANTIC RETRIEVAL EVALUATION")
    print("=" * 60)

    print(f"\nMean Recall@5: {result['mean_recall']:.2f}")

    for case in result["cases"]:
        print("\nTask:", case["task"])
        print("Query:", case["query"])
        print("Recall@5:", case["recall"])


if __name__ == "__main__":
    main()