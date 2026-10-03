from app.llm.qwen import QwenProvider


class ModelManager:
    def __init__(self):
        self._models = {}
        

    def get_model(self, model_name: str):
        if model_name not in self._models:
            self._models[model_name] = QwenProvider(model_name)

        return self._models[model_name]