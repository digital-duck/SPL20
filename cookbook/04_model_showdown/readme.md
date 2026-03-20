# Recipe 04 — Model Showdown

Same prompt to multiple Ollama models — compare output quality and latency side-by-side.

Uses parallel CTEs to fan out the prompt across models in a single SPL workflow, then generates a comparative evaluation.

## Usage

```bash
spl2 run cookbook/04_model_showdown/showdown.spl --adapter ollama \
    prompt="What is the meaning of life?"

spl2 run cookbook/04_model_showdown/showdown.spl --adapter ollama \
    prompt="Explain recursion in 3 sentences"
```

Override the models:
```bash
spl2 run cookbook/04_model_showdown/showdown.spl --adapter ollama prompt="Write a poem about Spring season" model_1=gemma3 model_2=phi3 model_3=qwen2.5
```

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `prompt`  | `What is the meaning of life?` | The question sent to all models |
| `model_1` | `gemma3`   | First model  |
| `model_2` | `llama3.2` | Second model |
| `model_3` | `mistral`  | Third model  |

## How it works

Three CTEs fan out the same prompt to each model in parallel. The results are collected into `@answer_1/2/3`, then a judge step synthesizes a side-by-side comparison highlighting strengths and differences.

This is the SPL 2.0 equivalent of Momahub's Recipe 08 (Model Arena) — but runs locally with zero infrastructure.
