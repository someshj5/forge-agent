class TaskComplexityClassifier:

    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"

    def classify(self, task: str) -> str:
        task_lower = task.lower()

        if any(keyword in task_lower for keyword in [
            "rename",
            "typo",
            "change variable",
            "update string",
            "small change",
        ]):
            return self.SIMPLE

        if any(keyword in task_lower for keyword in [
            "refactor",
            "architecture",
            "authentication",
            "migration",
            "multiple modules",
            "across modules",
        ]):
            return self.COMPLEX

        return self.MODERATE