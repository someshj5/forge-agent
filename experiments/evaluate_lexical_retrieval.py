
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.retrieval.cases import CASES,SEMANTIC_CASES

from evaluation.retrieval.lexical_baseline import evaluate_dataset

result = evaluate_dataset(CASES, k=5)

print(result)

result = evaluate_dataset(SEMANTIC_CASES, k=5)
print('-'*80)
print(result)