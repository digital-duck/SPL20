# SPL 2.0 Cookbook

Ready-to-run recipes demonstrating SPL 2.0 capabilities. Each recipe is self-contained.

## Prerequisites

```bash
conda create -n spl python=3.11
conda activate spl

pip install -e ".[dev]"          # install spl2
pip install httpx                # for ollama/openrouter/momagrid adapters

ollama pull gemma3               # at least one model
ollama serve                     # start ollama (if not running)
```

## Recipes

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 01 | Hello World | `hello.spl` | Minimal SPL program — verify spl2 + Ollama work | x |
| 02 | Ollama Proxy | `proxy.spl` | General-purpose LLM query — proxy any Ollama model | x |
| 03 | Multilingual | `multilingual.spl` | Greet in any language — parametric `lang` demo | x |
| 04 | Model Showdown | `showdown.sh` | Same prompt to multiple models, compare output and latency | x |
| 05 | Self-Refine | `self_refine.spl` | Iterative improvement: draft → critique → refine loop | x |
| 06 | ReAct Agent | `react_agent.spl` | Reasoning + Acting loop with tool-call pattern | x |
| 07 | Safe Generation | `safe_generation.spl` | Exception handling for production LLM safety | x |
| 08 | RAG Query | `rag_query.spl` | Retrieval-augmented generation over indexed documents | - |
| 09 | Chain of Thought | `chain.spl` | Multi-step reasoning: Research → Analyze → Summarize | - |
| 10 | Batch Test | `batch_test.sh` | Automated testing of multiple .spl scripts across models | x |


## Quick Smoke Test

```bash
# Parse all recipes (no LLM needed)
for f in cookbook/*/*.spl; do spl2 parse "$f"; done

# Run hello world with echo adapter (no Ollama needed)
spl2 run cookbook/01_hello_world/hello.spl

# Run with Ollama
spl2 run cookbook/01_hello_world/hello.spl --adapter ollama
```


### Test — Hello World

```bash
spl2 run cookbook/01_hello_world/hello.spl --adapter ollama
```

```
============================================================
Model: gemma3
Tokens: 38 in / 45 out
Latency: 1200ms
------------------------------------------------------------
Hello! I'm your friendly SPL 2.0 assistant. SPL (Structured Prompt Language)
is a declarative language for orchestrating LLM workflows — think SQL for AI.
============================================================
```


### Test — Ollama Proxy (any model, any prompt)

```bash
spl2 run cookbook/02_ollama_proxy/proxy.spl --adapter ollama -m gemma3 prompt="Explain quantum computing"
```

```
============================================================
Model: gemma3
Tokens: 44 in / 824 out
Latency: 12965ms
------------------------------------------------------------
Okay, let's break down quantum computing...
============================================================
```


### Test — Multilingual Greeting

```bash
spl2 run cookbook/03_multilingual/multilingual.spl --adapter ollama user_input="hello wen" lang="Chinese"
```

```
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 440ms
------------------------------------------------------------
你好，文！ (Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
```


### Test — Model Showdown (compare models)

```bash
bash cookbook/04_model_showdown/showdown.sh "What is the meaning of life?"
```


### Test — Self-Refining Agent

```bash
spl2 run cookbook/05_self_refine/self_refine.spl --adapter ollama -m gemma3 task="Write a haiku about coding"
```


### Test — Batch Test (all models x all recipes)

```bash
bash cookbook/10_batch_test/batch_test.sh
```
