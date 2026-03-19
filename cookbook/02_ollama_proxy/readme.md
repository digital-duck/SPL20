# Recipe 02 — Ollama Proxy

General-purpose LLM query — use any Ollama model from the command line with a single `.spl` file.

> `proxy.spl` is a symlink to `scripts/ollama_proxy.spl` — the canonical reusable script.
> Edit the source at `scripts/ollama_proxy.spl`.

## Usage

```bash
spl2 run scripts/ollama_proxy.spl --adapter ollama -m gemma3 prompt="Explain quantum computing"
spl2 run scripts/ollama_proxy.spl --adapter ollama -m llama3.2 prompt="Write a haiku about coding"
spl2 run scripts/ollama_proxy.spl --adapter ollama -m mistral prompt="What is 2+2?"
```

The `--model (-m)` flag overrides the model at runtime — no `.spl` edits needed. This makes it trivial to test any Ollama model:

```bash
for model in gemma3 llama3.2 mistral phi3 qwen2.5; do
  echo "=== $model ==="
  spl2 run scripts/ollama_proxy.spl --adapter ollama -m $model prompt="What is 2+2?"
done
```

Works with any adapter: `--adapter openrouter`, `--adapter momagrid`, `--adapter claude_cli`.

## Source

See [`scripts/ollama_proxy.spl`](../../scripts/ollama_proxy.spl) — also used by Recipe 04 (Model Showdown).
