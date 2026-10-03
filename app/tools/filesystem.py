from pathlib import Path

from app.config import WORKSPACE_ROOT


def resolve_workspace_path(path: str) -> Path:
    """
    Resolve a user/agent-provided path while ensuring
    it remains inside WORKSPACE_ROOT.
    """

    requested_path = (WORKSPACE_ROOT / path).resolve()

    try:
        requested_path.relative_to(WORKSPACE_ROOT)
    except ValueError:
        raise PermissionError(
            f"Access denied: path is outside workspace: {path}"
        )

    return requested_path


def read_file(path: str) -> dict:
    """
    Read a file from the agent workspace.
    """

    try:
        file_path = resolve_workspace_path(path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {path}",
            }

        if not file_path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {path}",
            }

        content = file_path.read_text(encoding="utf-8")

        return {
            "success": True,
            "path": path,
            "content": content,
            "line_count": len(content.splitlines()),
        }

    except PermissionError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    except UnicodeDecodeError:
        return {
            "success": False,
            "error": f"File is not valid UTF-8 text: {path}",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to read file: {exc}",
        }


def edit_file(
    path: str,
    old_text: str,
    new_text: str,
) -> dict:
    """
    Replace an exact piece of text inside a workspace file.
    """

    try:
        file_path = resolve_workspace_path(path)

        if not file_path.exists():
            return {
                "success": False,
                "error": f"File does not exist: {path}",
            }

        if not file_path.is_file():
            return {
                "success": False,
                "error": f"Path is not a file: {path}",
            }

        content = file_path.read_text(
            encoding="utf-8"
        )

        match_count = content.count(old_text)

        if match_count == 0:
            return {
                "success": False,
                "error": "Target text was not found.",
                "path": path,
            }

        if match_count > 1:
            return {
                "success": False,
                "error": (
                    "Target text matched multiple locations. "
                    "Edit was rejected to avoid an ambiguous change."
                ),
                "path": path,
                "match_count": match_count,
            }

        updated_content = content.replace(
            old_text,
            new_text,
            1,
        )

        file_path.write_text(
            updated_content,
            encoding="utf-8",
        )

        return {
            "success": True,
            "path": path,
            "message": "File edited successfully.",
            "match_count": 1,
        }

    except PermissionError as exc:
        return {
            "success": False,
            "error": str(exc),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to edit file: {exc}",
        }


def create_file(
    path: str,
    content: str,
) -> dict:
    """
    Create a new file inside the workspace.
    """

    try:
        file_path = resolve_workspace_path(path)

        if file_path.exists():
            return {
                "success": False,
                "error": f"File already exists: {path}",
            }

        file_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path.write_text(
            content,
            encoding="utf-8",
        )

        return {
            "success": True,
            "path": path,
            "message": "File created successfully.",
        }

    except PermissionError as exc:
        return {
            "success": False,
            "error_type": "PATH_SECURITY_VIOLATION",
            "error": str(exc),
            "requested_path": path,
            "hint": (
                "Use a repository-relative path under the workspace."
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": f"Failed to create file: {exc}",
        }