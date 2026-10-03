import pytest

from app.agent.actions import parse_action


def test_parse_valid_read_file_action():
    result = parse_action(
        '{"action":"read_file","arguments":{"path":"settings.py"}}'
    )

    assert result == {
        "action": "read_file",
        "arguments": {
            "path": "settings.py",
        },
    }


def test_reject_unknown_action():
    with pytest.raises(ValueError, match="Unknown action"):
        parse_action(
            '{"action":"delete_file","arguments":{"path":"x.py"}}'
        )


def test_reject_missing_argument():
    with pytest.raises(ValueError, match="Missing arguments"):
        parse_action(
            '{"action":"read_file","arguments":{}}'
        )


def test_reject_unexpected_argument():
    with pytest.raises(ValueError, match="Unexpected arguments"):
        parse_action(
            '{"action":"read_file","arguments":'
            '{"path":"x.py","dangerous":true}}'
        )


def test_parse_final_action():
    result = parse_action(
        '{"action":"final","arguments":{"message":"Done"}}'
    )

    assert result["action"] == "final"
    assert result["arguments"]["message"] == "Done"


def test_reject_invalid_json():
    with pytest.raises(ValueError, match="invalid JSON"):
        parse_action("this is not json")


def test_parse_markdown_json():
    result = parse_action(
        """```json
        {
            "action": "read_file",
            "arguments": {
                "path": "settings.py"
            }
        }
        ```"""
    )

    assert result["action"] == "read_file"
    assert result["arguments"]["path"] == "settings.py"

