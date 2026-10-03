from app.config import WORKSPACE_ROOT
from app.tools.execution import run_tests


def test_run_tests_success():

    result = run_tests(
        "demo-django"
    )

    assert result["success"] is True
    assert result["exit_code"] == 0


def test_run_tests_invalid_path():

    result = run_tests(
        "../../"
    )

    assert result["success"] is False


def test_run_tests_missing_project():

    result = run_tests(
        "does-not-exist"
    )

    assert result["success"] is False