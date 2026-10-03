from app.agent.actions import parse_action
from app.agent.state import AgentState
from app.agent.tools import TOOLS
from app.agent.verification import classify_test_result
from app.llm.manager import ModelManager
from app.llm.router import ModelRouter
from unittest.mock import patch
from app.context.engine import ContextEngine
from app.context.serializer import ContextSerializer

SYSTEM_PROMPT = """
You are a coding agent.

You MUST output exactly ONE JSON object.

Allowed actions:
- search_code
- read_file
- edit_file
- create_file
- run_tests
- final

Tool path rules:
- Paths are relative to the workspace root.
- The repository is "demo-django".
- Therefore repository paths must start with "demo-django".
- Never use absolute paths.
- Never use ".", "./", "..", "../", or other path traversal.
- Never guess an absolute filesystem path.

For repository "demo-django":
- Search the repository using path "demo-django".
- A file inside it uses paths such as "demo-django/demo_django/urls.py".

After receiving a tool result:
- If the result answers the task, return a "final" action.
- Do not repeat a successful tool call unnecessarily.
- Do not attempt another search just because the previous search succeeded.

Example:

{
  "action": "search_code",
  "arguments": {
    "query": "urlpatterns",
    "path": "demo-django"
  }
}

Final example:

{
  "action": "final",
  "arguments": {
    "message": "Found urlpatterns in demo-django/demo_django/urls.py."
  }
}

Output JSON only.
"""



class AgentLoop:

    def __init__(
        self,
        llm=None,
        max_iterations=10,
        max_invalid_actions=2,
        max_tool_failures=3,
        router=None,
        model_manager=None,
        context_engine=None,
        context_serializer=None,
        web_search_tool=None,
    ):
        self.llm = llm
        self.max_iterations = max_iterations
        self.max_invalid_actions = max_invalid_actions
        self.max_tool_failures = max_tool_failures

        self.router = router or ModelRouter()
        self.model_manager = model_manager or ModelManager()
        self.context_engine = context_engine or ContextEngine()
        self.context_serializer = context_serializer or ContextSerializer()
        self.web_search_tool = web_search_tool


    def run(
        self,
        task: str,
        repository: str,
    ) -> AgentState:

        state = AgentState(
            task=task,
            repository=repository,
            max_iterations=self.max_iterations,
        )

        context = self.context_engine.get_context(
            state.task,
            state.repository,
        )

        serialized_context = self.context_serializer.serialize(context)

        user_content = f"""Task:
{state.task}

Repository Context:
{serialized_context}"""


        state.messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT,
        },
        {
            "role": "user",
            "content": user_content,
        },
    ]


        while state.iteration < state.max_iterations:

            state.iteration += 1

            if self.llm is not None:
                llm = self.llm
            else:
                model_name = self.router.select_model(state)
                state.current_model = model_name

                llm = self.model_manager.get_model(model_name)

            response = llm.generate(
                state.messages,
                max_new_tokens=256,
                temperature=0.0,
            )

            state.messages.append(
                {
                    "role": "assistant",
                    "content": response,
                }
            )

            try:
                action = parse_action(response)

            except ValueError as exc:
                state.invalid_actions += 1

                if state.invalid_actions >= self.max_invalid_actions:
                    state.status = "failed"
                    state.final_message = (
                        "Agent stopped because the maximum number of "
                        "invalid actions was reached."
                    )
                    return state

                state.messages.append({
                    "role": "user",
                    "content": (
                        "Your previous response was invalid.\n"
                        f"Error: {exc}\n\n"
                        "Return ONLY valid JSON using the specified action schema."
                    ),
                })
                continue
            action_name = action["action"]
            arguments = action["arguments"]

            if action_name == "edit_file" and last_test_failed(state):
                state.repair_attempts += 1
                

                state.record_repair({
                    "attempt": state.repair_attempts,
                    "model": state.current_model,
                    "error_type": state.errors[-1]["type"],
                    "action": "edit_file",
                    "file": arguments["path"],
                    "result": "pending",
                    "edit_id": None,
                })


            if is_duplicate_tool_call(state, action_name, arguments):
                state.status = "failed"
                state.final_message = (
                    f"Agent attempted the same tool call twice: "
                    f"{action_name} {arguments}"
                )
                return state

            if action_name == "final":

                state.status = "completed"
                state.final_message = arguments["message"]

                return state

            tool = TOOLS[action_name]

            result = tool(**arguments)

            if action_name == "edit_file":
                edit_id = state.record_edit(
                    path=arguments["path"],
                    old_text=arguments["old_text"],
                    new_text=arguments["new_text"],
                    success=result.get("success", False),
                    error=result.get("error"),
                )

                if (
                    last_test_failed(state)
                    and state.repair_history
                    and state.repair_history[-1]["result"] == "pending"
                ):
                    state.repair_history[-1]["edit_id"] = edit_id

            if action_name == "run_tests":
                state.test_runs.append(result)

                error_type = classify_test_result(result)

                if error_type != "PASS":
                    state.errors.append({
                        "type": error_type,
                        "message": result.get("stderr") or result.get("error"),
                    })

                if state.repair_history and state.repair_history[-1]["result"] == "pending":
                    
                    if error_type == "PASS":
                        state.repair_history[-1]["result"] = "success"
                    else:
                        state.repair_history[-1]["result"] = "failed"

            elif action == "web_search":
                result = self.web_search_tool.search(
                    query=arguments["query"],
                    max_results=arguments.get("max_results", 5),
                )

            if not result.get("success", False):
                state.tool_failures += 1

                if state.tool_failures >= self.max_tool_failures:
                    state.status = "failed"
                    state.final_message = (
                        "Agent stopped because the maximum number of "
                        "tool failures was reached."
                    )
                    return state

            state.tool_calls.append(
                {
                    "action": action_name,
                    "arguments": arguments,
                    "result": result,
                }
            )

            if action_name == "search_code" and search_result_answers_task(
                state.task,
                result,
            ):
                state.status = "completed"

                matches = result.get("matches", [])

                state.final_message = (
                    f"Found matches for '{result.get('query')}'.\n"
                    + "\n".join(matches)
                )

                return state

            if not result.get("success", False):
                next_instruction = (
                    "The previous tool call failed.\n"
                    "Do not repeat the same failed action blindly.\n"
                    "Use the error to choose a recovery action.\n"
                    "Return ONLY the next JSON action."
                )
            else:
                next_instruction = (
                    "Tool execution succeeded.\n"
                    "Continue working on the task.\n"
                    "Return ONLY the next JSON action."
                )

            state.messages.append({
                "role": "user",
                "content": (
                    "Tool result:\n"
                    f"{result}\n\n"
                    f"{next_instruction}"
                ),
            })

            # state.messages.append(
            #     {
            #         "role": "user",
            #         "content": (
            #             "Tool result:\n"
            #             f"{result}\n\n"
            #             "Continue working on the task. "
            #             "Return ONLY the next JSON action."
            #         ),
            #     }
            # )

        # state.status = "max_iterations"
        state.status = "stopped"

        state.final_message = (
            "Agent stopped because the maximum number of iterations was reached."
        )

        return state

def is_duplicate_tool_call(state, action_name, arguments):
    for previous_call in state.tool_calls:
        if (
            previous_call["action"] == action_name
            and previous_call["arguments"] == arguments
            and previous_call["result"].get("success", False)
        ):
            return True

    return False


def search_result_answers_task(task: str, result: dict) -> bool:
    if not result.get("success"):
        return False

    if result.get("match_count", 0) == 0:
        return False

    query = result.get("query", "").lower()
    task_lower = task.lower()

    return query in task_lower


def last_test_failed(state: AgentState) -> bool:
    if not state.test_runs:
        return False

    return not state.test_runs[-1].get("success", False)

