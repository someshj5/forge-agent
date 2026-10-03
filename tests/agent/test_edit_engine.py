from unittest.mock import patch

from app.agent.edit_engine import EditEngine
from app.agent.edit_operations import (
    EditOperation,
    EditOperationType,
)


def test_insert_before():
    engine = EditEngine()

    operation = EditOperation(
        path="demo-django/demo_django/urls.py",
        target_id="A20",
        operation=EditOperationType.INSERT_BEFORE,
        text="# Django URL routes\n",
    )

    with patch(
        "app.agent.edit_engine.edit_file"
    ) as mock_edit:

        mock_edit.return_value = {
            "success": True,
        }

        result = engine.apply(
            operation,
            "urlpatterns = [",
        )

    mock_edit.assert_called_once_with(
        "demo-django/demo_django/urls.py",
        "urlpatterns = [",
        "# Django URL routes\nurlpatterns = [",
    )

    assert result["success"] is True


def test_insert_after():
    engine = EditEngine()

    operation = EditOperation(
        path="demo-django/demo_django/urls.py",
        target_id="A20",
        operation=EditOperationType.INSERT_AFTER,
        text="\n# Django URL routes",
    )

    with patch(
        "app.agent.edit_engine.edit_file"
    ) as mock_edit:

        mock_edit.return_value = {
            "success": True,
        }

        result = engine.apply(
            operation,
            "urlpatterns = [",
        )

    mock_edit.assert_called_once_with(
        "demo-django/demo_django/urls.py",
        "urlpatterns = [",
        "urlpatterns = [\n# Django URL routes",
    )

    assert result["success"] is True


def test_replace():
    engine = EditEngine()

    operation = EditOperation(
        path="example.py",
        target_id="A10",
        operation=EditOperationType.REPLACE,
        text="new_line",
    )

    with patch(
        "app.agent.edit_engine.edit_file"
    ) as mock_edit:

        mock_edit.return_value = {
            "success": True,
        }

        result = engine.apply(
            operation,
            "old_line",
        )

    mock_edit.assert_called_once_with(
        "example.py",
        "old_line",
        "new_line",
    )

    assert result["success"] is True


def test_delete():
    engine = EditEngine()

    operation = EditOperation(
        path="example.py",
        target_id="A10",
        operation=EditOperationType.DELETE,
    )

    with patch(
        "app.agent.edit_engine.edit_file"
    ) as mock_edit:

        mock_edit.return_value = {
            "success": True,
        }

        result = engine.apply(
            operation,
            "old_line",
        )

    mock_edit.assert_called_once_with(
        "example.py",
        "old_line",
        "",
    )

    assert result["success"] is True


def test_unsupported_operation():
    engine = EditEngine()

    operation = EditOperation(
        path="example.py",
        target_id="A10",
        operation="invalid",
    )

    result = engine.apply(
        operation,
        "old_line",
    )

    assert result["success"] is False
    assert "Unsupported edit operation" in result["error"]