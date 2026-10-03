import torch

from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"


def main():
    device = "mps" if torch.backends.mps.is_available() else "cpu"

    print(f"Model: {MODEL_NAME}")
    print(f"Device: {device}")
    print("Loading tokenizer...")

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    print("Loading model...")

    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        dtype=torch.float16,
    )

    model.to(device)
    model.eval()

    messages = [
    {
        "role": "system",
        "content": """
You are ForgeAgent, an AI coding agent.

You must choose exactly ONE action from this list:

1. search_code
2. read_file
3. edit_file
4. create_file
5. run_tests
6. final

Return ONLY valid JSON.

For search_code, use this schema:

{
  "action": "search_code",
  "arguments": {
    "query": "string",
    "path": "string"
  }
}

For read_file:

{
  "action": "read_file",
  "arguments": {
    "path": "string"
  }
}

For edit_file:

{
  "action": "edit_file",
  "arguments": {
    "path": "string",
    "old_text": "string",
    "new_text": "string"
  }
}

For create_file:

{
  "action": "create_file",
  "arguments": {
    "path": "string",
    "content": "string"
  }
}

For run_tests:

{
  "action": "run_tests",
  "arguments": {
    "project_path": "string"
  }
}

For final:

{
  "action": "final",
  "arguments": {
    "message": "string"
  }
}

Never invent action names.
Never add fields outside the specified schema.
""",
    },
    {
        "role": "user",
        "content": (
            "Find where Django URL routes are defined."
        ),
    },
]

    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
    )

    inputs = {
        key: value.to(device)
        for key, value in inputs.items()
    }

    print("Generating...")

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            do_sample=False,
        )

    generated_tokens = outputs[0][inputs["input_ids"].shape[1]:]

    response = tokenizer.decode(
        generated_tokens,
        skip_special_tokens=True,
    )

    print("\n--- MODEL RESPONSE ---")
    print(response)
    print("----------------------")


if __name__ == "__main__":
    main()