from app.agent.state import AgentState
from app.agents.coder_agent import CoderAgent
from app.agents.hub import HubAgent
from app.agents.search_agent import SearchAgent
from app.llm.qwen import QwenProvider
from pathlib import Path

from app.skills.registry import SkillRegistry
from app.skills.retriever import SkillRetriever
from app.skills.context import SkillContextLoader

def main():
    state = AgentState(
        task=(
            "Add the comment '# Django URL routes' "
            "immediately above urlpatterns."
        ),
        repository="demo-django",
    )

    print("=" * 70)
    print("FORGE AGENT - MULTI AGENT FLOW")
    print("=" * 70)

    skills_root = (
    Path.home()
        / ".agent"
        / "skills"
        / "skills"
    )

    skill_registry = SkillRegistry(
        skills_root=skills_root,
    )

    loaded = skill_registry.load()

    print(f"\nLoaded skills: {loaded}")

    skill_retriever = SkillRetriever(
        registry=skill_registry,
    )

    skill_context_loader = SkillContextLoader(
        registry=skill_registry,
    )


    search_agent = SearchAgent(
    skill_retriever=skill_retriever,
    skill_context_loader=skill_context_loader,
)

    llm = QwenProvider(
    model_name="Qwen/Qwen2.5-1.5B-Instruct"
)

    coder_agent = CoderAgent(
        llm=llm,
    )

    hub = HubAgent(
        agents={
            "search": search_agent,
            "code": coder_agent,
        }
    )

    # ---------------------------------------------------------
    # STEP 1 — Search
    # ---------------------------------------------------------

    print("\n[1] Running Hub")
    result = hub.run(state)

    print(f"Hub selected: {result.data.get('next_agent')}")
    print(f"Current agent: {state.current_agent}")

    if not result.success:
        print(f"ERROR: {result.error}")
        return

    print("\nRelevant files:")

    for path in state.relevant_files:
        print(f"  - {path}")

    print("\nSelected skills:")

    for skill in state.selected_skills:
        print(f"  - {skill}")

    print("\nSkill context loaded:")

    for skill in state.skill_context:
        print(f"  - {skill['name']}")

    # ---------------------------------------------------------
    # STEP 2 — Code
    # ---------------------------------------------------------

    print("\n[2] Running Hub")
    result = hub.run(state)

    print(f"Hub selected: {result.data.get('next_agent')}")
    print(f"Current agent: {state.current_agent}")

    if not result.success:
        print(f"ERROR: {result.error}")
        return

    print("\nEdits:")

    for edit in state.edits:
        print(f"  - {edit}")

    # ---------------------------------------------------------
    # STEP 3 — Show next state transition
    # ---------------------------------------------------------

    print("\n[3] Checking next Hub decision")

    next_agent = hub.decide_next_agent(state)

    print(f"Next agent would be: {next_agent}")

    print("\n" + "=" * 70)
    print("FLOW STOPPED FOR CHECKPOINT")
    print("=" * 70)

    print("\nFinal state:")
    print(f"  current_agent: {state.current_agent}")
    print(f"  relevant_files: {state.relevant_files}")
    print(f"  edits: {state.edits}")
    print(f"  test_runs: {state.test_runs}")


if __name__ == "__main__":
    main()