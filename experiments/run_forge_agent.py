from app.agent.loop import AgentLoop
from app.llm.qwen import QwenProvider

# MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"


def main():

    llm = QwenProvider(
        model_name=MODEL_NAME,
    )

    agent = AgentLoop(
        llm=llm,
        max_iterations=5,
    )

    state = agent.run(
        task=("Search for urlpatterns."),
        repository=("demo-django"),
    )

    print("\n========== AGENT RESULT ==========")

    print("Status:", state.status)
    print("Iterations:", state.iteration)

    print("\nTool calls:")

    for call in state.tool_calls:
        print(call)

    print("\nFinal message:")
    print(state.final_message)


if __name__ == "__main__":
    main()