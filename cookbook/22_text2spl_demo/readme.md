# Recipe 22: text2SPL Compiler Demo

Demonstrates the natural language → SPL 2.0 compiler. Given a plain-English description, `spl2 text2spl` generates valid SPL code and validates it with `spl2 parse`.

## Usage

```bash
bash cookbook/22_text2spl_demo/text2spl_demo.sh [adapter] [model]
```

Default adapter: `ollama`, default model: `gemma3`.

## Demos

| Demo | Mode | Input description |
|---|---|---|
| 1 | `prompt` | "summarize a document with a 2000 token budget" |
| 2 | `workflow` | "build a review agent that drafts, critiques, and refines text until quality > 0.8" |
| 3 | `auto` | "classify user intent and route to the right handler" |

## Modes

| Mode | Description |
|---|---|
| `prompt` | Generate a single GENERATE/PROMPT statement |
| `workflow` | Generate a multi-step WORKFLOW with procedures |
| `auto` | LLM decides the best form based on the description |

## Output

Generated `.spl` files are written to `cookbook/22_text2spl_demo/generated/` and validated with `spl2 parse`. To run a generated file:

```bash
spl2 run cookbook/22_text2spl_demo/generated/summarize.spl --adapter ollama
```
