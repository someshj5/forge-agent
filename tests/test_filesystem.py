from pathlib import Path
from app.tools.filesystem import edit_file
import pytest
from app.tools.filesystem import create_file
from app.config import WORKSPACE_ROOT
from app.tools.filesystem import (
    resolve_workspace_path,
    read_file,
)


def test_workspace_path():

    path = resolve_workspace_path("test.txt")

    assert path == WORKSPACE_ROOT / "test.txt"


def test_path_traversal_is_blocked():

    with pytest.raises(PermissionError):
        resolve_workspace_path("../../.env")


def test_read_file(tmp_path):

    test_file = WORKSPACE_ROOT / "hello.txt"
    test_file.write_text(
        "Hello ForgeAgent!",
        encoding="utf-8",
    )

    result = read_file("hello.txt")

    assert result["success"] is True
    assert result["content"] == "Hello ForgeAgent!"


def test_edit_file():

    test_file = WORKSPACE_ROOT / "edit_test.txt"

    test_file.write_text(
        "Hello world!",
        encoding="utf-8",
    )

    result = edit_file(
        "edit_test.txt",
        "Hello world!",
        "Hello ForgeAgent!",
    )

    assert result["success"] is True

    assert test_file.read_text(
        encoding="utf-8"
    ) == "Hello ForgeAgent!"


def test_edit_file_missing_target():

    test_file = WORKSPACE_ROOT / "edit_missing.txt"

    test_file.write_text(
        "Hello world!",
        encoding="utf-8",
    )

    result = edit_file(
        "edit_missing.txt",
        "Does not exist",
        "New text",
    )

    assert result["success"] is False


def test_edit_file_ambiguous_match():

    test_file = WORKSPACE_ROOT / "edit_ambiguous.txt"

    test_file.write_text(
        "hello\nhello\n",
        encoding="utf-8",
    )

    result = edit_file(
        "edit_ambiguous.txt",
        "hello",
        "goodbye",
    )

    assert result["success"] is False
    assert result["match_count"] == 2


def test_create_file():

    test_file = WORKSPACE_ROOT / "created_test.py"

    if test_file.exists():
        test_file.unlink()

    result = create_file(
        "created_test.py",
        "print('hello')\n",
    )

    assert result["success"] is True

    assert test_file.exists()

    assert test_file.read_text(
        encoding="utf-8"
    ) == "print('hello')\n"


def test_create_existing_file():

    test_file = WORKSPACE_ROOT / "existing.txt"

    test_file.write_text(
        "existing",
        encoding="utf-8",
    )

    result = create_file(
        "existing.txt",
        "new content",
    )

    assert result["success"] is False
