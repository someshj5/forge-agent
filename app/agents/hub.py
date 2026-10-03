from app.agents.base import Agent, AgentResult


class HubAgent(Agent):
    name = "hub"

    SEARCH = "search"
    CODE = "code"
    TEST = "test"
    REPAIR = "repair"
    FINAL = "final"
    FAILED = "failed"

    def __init__(self, agents=None):
        self.agents = agents or {}

    def decide_next_agent(self, state) -> str:
        # Initial task
        if not state.relevant_files:
            return self.SEARCH

        # We have context but no edits yet
        if not state.edits:
            return self.CODE

        # We have edits but haven't verified them
        if not state.test_runs:
            return self.TEST

        last_test = state.test_runs[-1]

        # Tests passed
        if last_test.get("success"):
            return self.FINAL

        # Tests failed and repair budget remains
        if state.repair_attempts < state.max_repair_attempts:
            return self.REPAIR

        return self.FAILED

    def run(self, state) -> AgentResult:
        next_agent = self.decide_next_agent(state)

        state.next_agent = next_agent
        state.current_agent = self.name

        # Terminal states
        if next_agent == self.FINAL:
            return AgentResult(
                success=True,
                agent=self.name,
                data={
                    "next_agent": next_agent,
                },
            )

        if next_agent == self.FAILED:
            return AgentResult(
                success=False,
                agent=self.name,
                data={
                    "next_agent": next_agent,
                },
            )

        # Routing-only mode
        #
        # This allows the Hub to be used purely as a
        # deterministic state transition component.
        if not self.agents:
            return AgentResult(
                success=True,
                agent=self.name,
                data={
                    "next_agent": next_agent,
                },
            )

        # Delegation mode
        agent = self.agents.get(next_agent)

        if agent is None:
            return AgentResult(
                success=False,
                agent=self.name,
                data={
                    "next_agent": next_agent,
                },
                error=f"No agent registered for '{next_agent}'",
            )

        result = agent.run(state)

        return AgentResult(
            success=result.success,
            agent=self.name,
            data={
                "next_agent": next_agent,
                "agent_result": result,
            },
            error=result.error,
        )