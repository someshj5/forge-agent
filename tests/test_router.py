from unittest.mock import Mock

from app.agent.state import AgentState
from app.llm.router import ModelRouter


def test_router_selects_small_model_for_new_task():
    state = AgentState(
        task="Rename a variable",
        repository="demo-django",
        repair_attempts=0,
    )

    router = ModelRouter()

    model = router.select_model(state)

    assert model == "Qwen/Qwen2.5-0.5B-Instruct"


def test_router_escalates_after_repair_attempt():
    state = AgentState(
        task="Fix failing tests",
        repository="demo-django",
        repair_attempts=1,
    )

    router = ModelRouter()

    model = router.select_model(state)

    assert model == "Qwen/Qwen2.5-1.5B-Instruct"


def test_router_stays_on_strong_model_after_multiple_repairs():
    state = AgentState(
        task="Fix authentication",
        repository="demo-django",
        repair_attempts=3,
    )

    router = ModelRouter()

    model = router.select_model(state)

    assert model == "Qwen/Qwen2.5-1.5B-Instruct"


def test_repair_attempt_takes_precedence_over_complexity():
    state = AgentState(
        task="Rename variable x to y",
        repository="demo-django",
        repair_attempts=1,
    )

    classifier = Mock()

    router = ModelRouter(
        complexity_classifier=classifier
    )

    assert router.select_model(state) == "Qwen/Qwen2.5-1.5B-Instruct"

    classifier.classify.assert_not_called()