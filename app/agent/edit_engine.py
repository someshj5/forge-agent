from app.agent.edit_operations import (
    EditOperation,
    EditOperationType,
)
from app.tools.filesystem import edit_file


class EditEngine:
    """
    Deterministic translation layer between semantic edit operations
    and the low-level edit_file() primitive.
    """

    def apply(
        self,
        operation: EditOperation,
        target_text: str,
    ) -> dict:
        """
        Convert a semantic edit operation into an exact file edit.
        """

        if operation.operation == EditOperationType.INSERT_BEFORE:
            new_text = f"{operation.text}{target_text}"

        elif operation.operation == EditOperationType.INSERT_AFTER:
            new_text = f"{target_text}{operation.text}"

        elif operation.operation == EditOperationType.REPLACE:
            new_text = operation.text

        elif operation.operation == EditOperationType.DELETE:
            new_text = ""

        else:
            return {
                "success": False,
                "error": (
                    f"Unsupported edit operation: "
                    f"{operation.operation}"
                ),
            }

        return edit_file(
            operation.path,
            target_text,
            new_text,
        )