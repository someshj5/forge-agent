from app.agents.base import Agent, AgentResult
from app.agents.permissions import is_allowed


def test_agent_result_defaults():
    result = AgentResult(
        success=True,
        agent="search",
    )

    assert result.success is True
    assert result.agent == "search"
    assert result.data == {}
    assert result.error is None


class FakeAgent(Agent):
    name = "fake"

    def run(self, state):
        return AgentResult(
            success=True,
            agent=self.name,
        )


def test_agent_can_be_implemented():
    agent = FakeAgent()

    result = agent.run(None)

    assert result.success is True
    assert result.agent == "fake"


def test_search_agent_can_web_search():
    assert is_allowed("search", "web_search")


def test_coder_agent_can_web_search():
    assert is_allowed("coder", "web_search")


def test_tester_agent_cannot_web_search():
    assert not is_allowed("tester", "web_search")