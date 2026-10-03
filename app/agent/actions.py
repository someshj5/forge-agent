import json

from app.agent.tools import TOOLS


ACTION_SCHEMAS = {
    "search_code": {"query", "path"},
    "read_file": {"path"},
    "edit_file": {"path", "old_text", "new_text"},
    "create_file": {"path", "content"},
    "run_tests": {"project_path"},
    "final": {"message"},
    "web_search": {
    "required": ["query"],
    "optional": ["max_results"],},
}

def clean_model_output(raw_output: str) -> str:
    """
    Remove harmless Markdown code fences from model output.
    """

    output = raw_output.strip()

    if output.startswith("```json"):
        output = output[len("```json"):].strip()

    elif output.startswith("```"):
        output = output[len("```"):].strip()

    if output.endswith("```"):
        output = output[:-3].strip()

    return output

def parse_action(raw_output: str) -> dict:
    """
    Parse and validate an LLM action.

    Returns a normalized action dictionary.

    Raises:
        ValueError: if the model output is invalid.
    """

    cleaned_output = clean_model_output(raw_output)

    try:
        action = json.loads(cleaned_output)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Model returned invalid JSON: {exc}"
        ) from exc
    
    action_name = action.get("action")

    if not isinstance(action_name, str):
        raise ValueError("Missing or invalid 'action'.")

    if action_name == "final":
        allowed_arguments = ACTION_SCHEMAS["final"]
    else:
        if action_name not in TOOLS:
            raise ValueError(
                f"Unknown action: {action_name}"
            )

        allowed_arguments = ACTION_SCHEMAS[action_name]

    arguments = action.get("arguments")

    if not isinstance(arguments, dict):
        raise ValueError(
            "'arguments' must be a JSON object."
        )

    missing = allowed_arguments - arguments.keys()

    if missing:
        raise ValueError(
            f"Missing arguments for '{action_name}': "
            f"{sorted(missing)}"
        )

    unexpected = arguments.keys() - allowed_arguments

    if unexpected:
        raise ValueError(
            f"Unexpected arguments for '{action_name}': "
            f"{sorted(unexpected)}"
        )

    return {
        "action": action_name,
        "arguments": arguments,
    }