from app.llm.complexity import TaskComplexityClassifier


class ModelRouter:
    SMALL_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
    MEDIUM_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"
    STRONG_MODEL = "Qwen/Qwen2.5-1.5B-Instruct"

    def __init__(self, complexity_classifier=None):
        self.complexity_classifier = (
            complexity_classifier
            or TaskComplexityClassifier()
        )

    def select_model(self, state):
        # Repair evidence takes precedence over initial complexity.
        if state.repair_attempts >= 1:
            return self.STRONG_MODEL

        complexity = self.complexity_classifier.classify(state.task)

        if complexity == TaskComplexityClassifier.SIMPLE:
            return self.SMALL_MODEL

        if complexity == TaskComplexityClassifier.MODERATE:
            return self.MEDIUM_MODEL

        if complexity == TaskComplexityClassifier.COMPLEX:
            return self.STRONG_MODEL

        raise ValueError(
            f"Unknown task complexity: {complexity}"
        )