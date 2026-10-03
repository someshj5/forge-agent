from app.llm.complexity import TaskComplexityClassifier


def test_simple_task():
    classifier = TaskComplexityClassifier()

    assert classifier.classify(
        "Rename variable x to y"
    ) == classifier.SIMPLE


def test_moderate_task():
    classifier = TaskComplexityClassifier()

    assert classifier.classify(
        "Add a Django endpoint and tests"
    ) == classifier.MODERATE


def test_complex_task():
    classifier = TaskComplexityClassifier()

    assert classifier.classify(
        "Refactor authentication across modules"
    ) == classifier.COMPLEX


def test_unknown_task_defaults_to_moderate():
    classifier = TaskComplexityClassifier()

    assert classifier.classify(
        "Fix this bug"
    ) == classifier.MODERATE