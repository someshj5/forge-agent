from dataclasses import dataclass
from time import perf_counter

from app.agent.state import AgentState
from app.agents.base import AgentResult
from app.agents.coder_agent import CoderAgent
from app.agents.hub import HubAgent
from app.agents.orchestrator import AgentOrchestrator
from app.agents.search_agent import SearchAgent


TASK = (
    "Add the comment '# Django URL routes' "
    "immediately above urlpatterns."
)

REPOSITORY = "demo-django"


@dataclass(frozen=True)
class ExperimentConfig:
    name: str
    use_skills: bool


@dataclass
class ExperimentResult:
    experiment: str
    selected_skills: list[str]
    status: str
    edit_success: bool
    pytest_success: bool
    repair_attempts: int
    iterations: int
    latency_ms: float


BASELINE = ExperimentConfig(
    name="baseline",
    use_skills=False,
)

SKILL_AUGMENTED = ExperimentConfig(
    name="django-pro",
    use_skills=True,
)


class FakeContextEngine:
    """
    Deterministic repository retrieval.

    We keep repository context identical between A and B.
    """

    def get_context(self, query, repository):
        return [
            {
                "path": "demo-django/demo_django/urls.py",
                "score": 5,
                "source": "lexical",
                "content": (
                    "from django.contrib import admin\n"
                    "from django.urls import path\n\n"
                    "urlpatterns = [\n"
                    "    path('admin/', admin.site.urls),\n"
                    "]\n"
                ),
            }
        ]


class FakeSkillRetriever:
    """
    Deterministic skill selection.

    The experiment controls whether this retriever is used.
    """

    def retrieve(self, query, limit=3):
        skill = type(
            "Skill",
            (),
            {
                "name": "django-pro",
            },
        )()

        return [
            type(
                "SkillSearchResult",
                (),
                {
                    "skill": skill,
                },
            )()
        ]


class FakeSkillContextLoader:

    def load_many(self, skills):
        return [
            {
                "name": "django-pro",
                "description": (
                    "Django development guidance."
                ),
                "content": (
                    "Use standard Django URL routing patterns. "
                    "Keep URL configuration explicit and readable."
                ),
            }
            for skill in skills
        ]


class FakeLLM:
    """
    Deterministic coder model.

    This first experiment validates the skill plumbing and
    evaluation pipeline rather than measuring model quality.
    """

    def __init__(self):
        self.calls = []

    def generate(self, messages, **kwargs):
        self.calls.append(messages)

        return """
{
    "operation": "insert_before",
    "text": "# Django URL routes\\n"
}
"""


class FakeTester:
    """
    Deterministic tester for the first experiment.

    The real TesterAgent will replace this once the
    evaluation plumbing is validated.
    """

    name = "tester"

    def run(self, state):
        state.test_runs.append(
            {
                "success": True,
                "returncode": 0,
            }
        )

        return AgentResult(
            success=True,
            agent=self.name,
        )


def build_search_agent(use_skills: bool):
    if use_skills:
        return SearchAgent(
            context_engine=FakeContextEngine(),
            skill_retriever=FakeSkillRetriever(),
            skill_context_loader=FakeSkillContextLoader(),
        )

    return SearchAgent(
        context_engine=FakeContextEngine(),
    )


def build_coder_agent():
    return CoderAgent(
        llm=FakeLLM(),
    )


def run_experiment(config: ExperimentConfig) -> ExperimentResult:
    state = AgentState(
        task=TASK,
        repository=REPOSITORY,
    )

    search_agent = build_search_agent(
        use_skills=config.use_skills,
    )

    coder_agent = build_coder_agent()

    tester_agent = FakeTester()

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": coder_agent,
            "test": tester_agent,
        }
    )

    orchestrator = AgentOrchestrator(
        hub=hub,
    )

    started = perf_counter()

    result = orchestrator.run(state)

    elapsed_ms = (
        perf_counter() - started
    ) * 1000

    edit_success = bool(
        state.edits
        and state.edits[-1].get("success")
    )

    pytest_success = bool(
        state.test_runs
        and state.test_runs[-1].get("success")
    )

    return ExperimentResult(
        experiment=config.name,
        selected_skills=state.selected_skills,
        status=result.status,
        edit_success=edit_success,
        pytest_success=pytest_success,
        repair_attempts=state.repair_attempts,
        iterations=state.iteration,
        latency_ms=round(elapsed_ms, 2),
    )


def print_result(result: ExperimentResult):
    print()
    print("=" * 60)
    print(result.experiment)
    print("=" * 60)

    print(
        f"selected_skills : {result.selected_skills}"
    )
    print(
        f"status          : {result.status}"
    )
    print(
        f"edit_success    : {result.edit_success}"
    )
    print(
        f"pytest_success  : {result.pytest_success}"
    )
    print(
        f"repair_attempts : {result.repair_attempts}"
    )
    print(
        f"iterations      : {result.iterations}"
    )
    print(
        f"latency_ms      : {result.latency_ms}"
    )


if __name__ == "__main__":
    baseline = run_experiment(BASELINE)

    augmented = run_experiment(
        SKILL_AUGMENTED
    )

    print_result(baseline)
    print_result(augmented)