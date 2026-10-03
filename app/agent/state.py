from dataclasses import dataclass, field

TERMINAL_STATUSES = {
    "completed",
    "failed",
    "stopped",
}

@dataclass
class AgentState:
    task: str
    repository: str

    messages: list[dict] = field(default_factory=list)

    tool_calls: list[dict] = field(default_factory=list)

    iteration: int = 0
    max_iterations: int = 10

    status: str = "running"

    final_message: str | None = None
    invalid_actions: int = 0
    tool_failures: int = 0

    plan: list[str] = field(default_factory=list)
    relevant_files: list[str] = field(default_factory=list)
    target_symbol: str | None = None
    edits: list[dict] = field(default_factory=list)
    test_runs: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    repair_attempts: int = 0
    max_repair_attempts: int = 3
    current_model: str | None = None
    repair_history: list[dict] = field(default_factory=list)
    status: str = "running"
    selected_skills: list[str] = field(default_factory=list)
    skill_context: list[dict] = field(default_factory=list)


    def record_repair(self, repair: dict) -> None:
        self.repair_history.append(repair)

    def record_edit(self,path: str,old_text: str,new_text: str,success: bool,error: str | None = None,) -> str:
        edit_id = f"edit-{len(self.edits) + 1}"

        self.edits.append({
            "id": edit_id,
            "path": path,
            "old_text": old_text,
            "new_text": new_text,
            "success": success,
            "error": error,
        })

        return edit_id