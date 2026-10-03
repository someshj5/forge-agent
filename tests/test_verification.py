from app.agent.verification import classify_test_result


def test_classify_success():
    result = {
        "success": True,
        "stdout": "",
        "stderr": "",
    }

    assert classify_test_result(result) == "PASS"


def test_classify_syntax_error():
    result = {
        "success": False,
        "stdout": "",
        "stderr": "SyntaxError: invalid syntax",
    }

    assert classify_test_result(result) == "SYNTAX_ERROR"


def test_classify_import_error():
    result = {
        "success": False,
        "stdout": "",
        "stderr": "ModuleNotFoundError: No module named 'foo'",
    }

    assert classify_test_result(result) == "IMPORT_ERROR"


def test_classify_test_failure():
    result = {
        "success": False,
        "stdout": "",
        "stderr": "AssertionError: Expected 200, got 500",
    }

    assert classify_test_result(result) == "TEST_FAILURE"