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
| 11 | Debate Arena | `debate.spl` | Adversarial debate between two LLM personas with a judge | - |
| 12 | Plan and Execute | `plan_execute.spl` | Planner decomposes task into steps, executor runs each one | - |
| 13 | Map-Reduce | `map_reduce.spl` | Split large docs into chunks, summarize each, combine results | - |
| 14 | Multi-Agent | `multi_agent.spl` | Researcher → Analyst → Writer collaboration via PROCEDURE | - |
| 15 | Code Review | `code_review.spl` | Multi-pass review: security, performance, style, bugs | - |
| 16 | Reflection | `reflection.spl` | Meta-cognitive loop: solve → reflect → correct until confident | - |
| 17 | Tree of Thought | `tree_of_thought.spl` | Explore multiple reasoning paths, score and pick the best | - |
| 18 | Guardrails | `guardrails.spl` | Input/output safety pipeline with PII detection and filtering | - |
| 19 | Memory Chat | `memory_chat.spl` | Persistent memory across conversations via memory.get/set | - |
| 20 | Ensemble Voting | `ensemble.spl` | Generate multiple answers, score and vote for consensus | - |
| 21 | Multi-Model Pipeline | `multi_model.spl` | Per-step model selection with GENERATE...USING MODEL and quality loop | - |
| 22 | Text2SPL Demo | `text2spl_demo.sh` | Natural language to SPL 2.0 compiler — prompt, workflow, and auto modes | - |


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


### Test — Multi-Model Pipeline (per-step model selection)

```bash
spl2 run cookbook/21_multi_model_pipeline/multi_model.spl --adapter ollama topic="climate change"
```

This recipe showcases `GENERATE ... USING MODEL` — each step can target a different model within the same workflow.


### Test — Text2SPL Demo (NL → SPL compiler)

```bash
bash cookbook/22_text2spl_demo/text2spl_demo.sh
```

Demonstrates the `spl2 text2spl` / `spl2 compile` command: natural language descriptions compiled into valid SPL 2.0 code with automatic validation.


### Test — Batch Test (all models x all recipes)

```bash
bash cookbook/10_batch_test/batch_test.sh
```
