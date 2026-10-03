from app.agents.hub import HubAgent
from app.agent.state import AgentState


class AgentOrchestrator:
    """
    Deterministic execution loop around HubAgent.

    The Hub decides which specialist should run next.
    The orchestrator executes that transition repeatedly
    until the workflow reaches FINAL or FAILED.
    """

    def __init__(
        self,
        hub: HubAgent,
        max_steps: int = 20,
    ):
        self.hub = hub
        self.max_steps = max_steps

    def run(self, state: AgentState) -> AgentState:
        for _ in range(self.max_steps):
            state.iteration += 1

            result = self.hub.run(state)

            next_agent = result.data.get("next_agent")

            if next_agent == self.hub.FINAL:
                state.status = "completed"
                return state

            if next_agent == self.hub.FAILED:
                state.status = "failed"

                if result.error:
                    state.final_message = result.error

                return state

            if not result.success:
                state.status = "failed"
                state.final_message = result.error
                return state

        state.status = "failed"
        state.final_message = (
            "Orchestrator stopped because the maximum "
            "number of steps was reached."
        )

        return state