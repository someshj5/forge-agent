import subprocess

from app.config import WORKSPACE_ROOT


def search_code(query: str, path: str = ".") -> dict:
    """
    Search source code inside the agent workspace using ripgrep.
    """

    search_path = (WORKSPACE_ROOT / path).resolve()

    try:
        search_path.relative_to(WORKSPACE_ROOT)
    except ValueError:
        return {
            "success": False,
            "error": f"Search path is outside workspace: {path}",
        }

    try:
        result = subprocess.run(
            [
                "rg",
                "--line-number",
                "--no-heading",
                "--color",
                "never",
                query,
                str(search_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 1:
            return {
                "success": True,
                "matches": [],
                "message": "No matches found.",
            }

        if result.returncode != 0:
            return {
                "success": False,
                "error": result.stderr.strip(),
            }

        matches = []

        workspace_prefix = str(WORKSPACE_ROOT) + "/"

        for line in result.stdout.splitlines():
            if line.startswith(workspace_prefix):
                line = line[len(workspace_prefix):]

            matches.append(line)

        return {
            "success": True,
            "query": query,
            "matches": matches,
            "match_count": len(matches),
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": "ripgrep (rg) is not installed.",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Search timed out.",
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
        }