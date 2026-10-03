from unittest.mock import Mock

from app.agent.loop import AgentLoop
from app.agent.state import AgentState
from app.llm.router import ModelRouter


def test_agent_uses_strong_model_after_repair():
    router = ModelRouter()

    state = AgentState(
        task="Rename variable x to ys",
        repository="demo-django",
        repair_attempts=0,
    )

    first_model = router.select_model(state)

    assert first_model == "Qwen/Qwen2.5-0.5B-Instruct"

    # Simulate a failed verification followed by a repair.
    state.repair_attempts = 1

    second_model = router.select_model(state)

    assert second_model == "Qwen/Qwen2.5-1.5B-Instruct"
