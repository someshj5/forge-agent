import torch

from transformers import AutoModelForCausalLM, AutoTokenizer

from app.llm.base import LLMProvider


class QwenProvider(LLMProvider):

    def __init__(
        self,
        model_name: str,
        device: str | None = None,
    ):
        self.model_name = model_name

        if device is None:
            device = "mps" if torch.backends.mps.is_available() else "cpu"

        self.device = device

        print(f"Loading model: {model_name}")
        print(f"Device: {self.device}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
        )

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
        )

        self.model.to(self.device)
        self.model.eval()

    def generate(
        self,
        messages: list[dict],
            max_new_tokens: int = 256,
            temperature: float = 0.0,
            **kwargs,
        ) -> str:

        print("\n========== MODEL MESSAGES ==========")
        for message in messages:
            print(f"\n[{message['role']}]")
            print(message["content"])
        print("====================================\n")

        prompt = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        generation_kwargs = {
            "max_new_tokens": max_new_tokens,
            "do_sample": temperature > 0,
        }

        if temperature > 0:
            generation_kwargs["temperature"] = temperature

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                **generation_kwargs,
            )

        generated_tokens = outputs[0][
            inputs["input_ids"].shape[1]:
        ]

        response = self.tokenizer.decode(
            generated_tokens,
            skip_special_tokens=True,
        )

        return response.strip()