AGENT_PERMISSIONS = {
    "search": {
        "search_code",
        "web_search",
    },
    "coder": {
        "read_file",
        "edit_file",
        "create_file",
        "web_search",
    },
    "tester": {
        "run_tests",
    },
    "repair": {
        "read_file",
        "edit_file",
        "run_tests",
        "web_search",
    },
}

def is_allowed(agent_name: str, tool_name: str) -> bool:
    return tool_name in AGENT_PERMISSIONS.get(
        agent_name,
        set(),
    )