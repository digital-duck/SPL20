# Recipe 04 — Model Showdown

Same prompt to multiple Ollama models — compare output quality and latency side-by-side.

## Usage

```bash
bash cookbook/04_model_showdown/showdown.sh "What is the meaning of life?"
bash cookbook/04_model_showdown/showdown.sh "Explain recursion in 3 sentences"
```

Override the model list:
```bash
MODELS="gemma3 llama3.2 mistral phi3 qwen2.5" bash cookbook/04_model_showdown/showdown.sh "Write a haiku"
```

This is the SPL 2.0 equivalent of Momahub's Recipe 08 (Model Arena) — but runs locally with zero infrastructure.
