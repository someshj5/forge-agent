class ContextSerializer:
    def serialize(self, context: list[dict]) -> str:
        if not context:
            return ""

        output = []

        for item in context:
            res = f"""### File: {item['path']}
                    ```python
                    {item['content']}
                    ```"""
            output.append(res)

        return "\n\n".join(output)