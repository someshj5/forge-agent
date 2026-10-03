def classify_test_result(result: dict) -> str:
    if result.get("success"):
        return "PASS"

    if result.get("error"):
        error = result["error"].lower()

        if "timed out" in error:
            return "TIMEOUT"

        return "EXECUTION_ERROR"

    stderr = result.get("stderr", "").lower()

    if "syntaxerror" in stderr:
        return "SYNTAX_ERROR"

    if "modulenotfounderror" in stderr:
        return "IMPORT_ERROR"

    if "assertionerror" in stderr:
        return "TEST_FAILURE"

    return "TEST_FAILURE"