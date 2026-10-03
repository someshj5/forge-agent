from unittest.mock import patch

from app.llm.manager import ModelManager


def test_model_manager_loads_model():
    manager = ModelManager()

    with patch("app.llm.manager.QwenProvider") as mock_provider:
        model = manager.get_model("Qwen/Qwen2.5-0.5B-Instruct")

        mock_provider.assert_called_once_with(
            "Qwen/Qwen2.5-0.5B-Instruct"
        )

        assert model is mock_provider.return_value


def test_model_manager_reuses_cached_model():
    manager = ModelManager()

    with patch("app.llm.manager.QwenProvider") as mock_provider:
        first = manager.get_model("Qwen/Qwen2.5-0.5B-Instruct")
        second = manager.get_model("Qwen/Qwen2.5-0.5B-Instruct")

        assert first is second

        mock_provider.assert_called_once_with(
            "Qwen/Qwen2.5-0.5B-Instruct"
        )


def test_model_manager_keeps_different_models_separate():
    manager = ModelManager()

    with patch("app.llm.manager.QwenProvider") as mock_provider:
        small_provider = object()
        strong_provider = object()

        mock_provider.side_effect = [
            small_provider,
            strong_provider,
        ]

        small = manager.get_model(
            "Qwen/Qwen2.5-0.5B-Instruct"
        )

        strong = manager.get_model(
            "Qwen/Qwen2.5-1.5B-Instruct"
        )

        assert small is small_provider
        assert strong is strong_provider
        assert small is not strong

        assert mock_provider.call_count == 2