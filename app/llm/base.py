from abc import ABC, abstractmethod


class LLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        messages: list[dict],
        **kwargs,
    ) -> str:
        """
        Generate a response from the model.

        messages:
            [
                {"role": "system", "content": "..."},
                {"role": "user", "content": "..."},
            ]

        Returns:
            Raw model response as a string.
        """
        raise NotImplementedError