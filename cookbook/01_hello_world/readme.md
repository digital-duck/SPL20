# Recipe 01: Hello World

Minimal SPL program — verifies that `spl2`, the chosen adapter, and the model are all wired up correctly. No parameters required.

## Usage

```bash
# Echo adapter (no LLM needed — mirrors prompt back)
spl2 run cookbook/01_hello_world/hello.spl

# Local Ollama
spl2 run cookbook/01_hello_world/hello.spl --adapter ollama

# Specific model
spl2 run cookbook/01_hello_world/hello.spl --adapter ollama -m gemma3

# Claude Code CLI
spl2 run cookbook/01_hello_world/hello.spl --adapter claude_cli
```

## What it does

Sends a single `GENERATE greeting()` with a system role instructing the model to introduce itself and SPL 2.0 in two sentences.
