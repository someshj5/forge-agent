from unittest.mock import Mock

from app.agent.loop import AgentLoop
from app.agent.state import AgentState
from app.llm.manager import ModelManager
from app.llm.router import ModelRouter


def test_router_escalates_after_repair():
    router = ModelRouter()

    state = AgentState(
        task="Rename variable x to y",
        repository="demo-django",
        repair_attempts=0,
    )

    first_model = router.select_model(state)

    assert first_model == "Qwen/Qwen2.5-0.5B-Instruct"

    state.repair_attempts = 1

    second_model = router.select_model(state)

    assert second_model == "Qwen/Qwen2.5-1.5B-Instruct"

def test_router_and_manager_use_different_models_after_escalation():
    router = ModelRouter()

    small_model = Mock()
    strong_model = Mock()

    manager = ModelManager()

    manager._models = {
        "Qwen/Qwen2.5-0.5B-Instruct": small_model,
        "Qwen/Qwen2.5-1.5B-Instruct": strong_model,
    }

    state = AgentState(
        task="Rename variable x to y",
        repository="demo-django",
        repair_attempts=0,
    )

    model_name = router.select_model(state)
    provider = manager.get_model(model_name)

    assert model_name == "Qwen/Qwen2.5-0.5B-Instruct"
    assert provider is small_model

    state.repair_attempts = 1

    model_name = router.select_model(state)
    provider = manager.get_model(model_name)

    assert model_name == "Qwen/Qwen2.5-1.5B-Instruct"
    assert provider is strong_model



