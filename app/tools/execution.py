import subprocess

from app.config import WORKSPACE_ROOT


def run_tests(
    project_path: str,
    timeout: int = 30,
) -> dict:
    """
    Run pytest inside a project contained within the workspace.
    """

    project_root = (
        WORKSPACE_ROOT / project_path
    ).resolve()

    try:
        project_root.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return {
            "success": False,
            "error": (
                f"Project path is outside workspace: "
                f"{project_path}"
            ),
        }

    if not project_root.exists():
        return {
            "success": False,
            "error": (
                f"Project does not exist: "
                f"{project_path}"
            ),
        }

    if not project_root.is_dir():
        return {
            "success": False,
            "error": (
                f"Project path is not a directory: "
                f"{project_path}"
            ),
        }

    try:
        result = subprocess.run(
            ["pytest"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        return {
            "success": result.returncode == 0,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": (
                f"Tests timed out after {timeout} seconds."
            ),
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }