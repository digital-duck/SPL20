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

## Run All

```bash

python cookbook/run_all.py 2>&1 | tee cookbook/out/run_all_$(date +%Y%m%d_%H%M%S).md 

# retry failed recipes
python cookbook/run_all.py --ids "04,10, 23-35" 2>&1 | tee cookbook/out/run_all_failed-$(date +%Y%m%d_%H%M%S).md 

python cookbook/run_all.py --ids "04,10, 25,26, 29,30, 32,33" 2>&1 | tee cookbook/out/run_all_failed-$(date +%Y%m%d_%H%M%S).md 


```

## Code-RAG

Run 
```bash
spl2 code-rag parse-log cookbook/out/run_all_20260320_052826.md 
```
once the run finishes to capture all 30 new  (prompt, SPL) pairs into Code-RAG       



## Recipes

Status: `✓` done · `-` parser/runtime pending · `todo` not yet written

### Tier 1 — Core SPL (Language Fundamentals)

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 01 | Hello World | `hello.spl` | Minimal SPL program — verify spl2 + Ollama work | ✓ |
| 02 | Ollama Proxy | `proxy.spl` | General-purpose LLM query — proxy any Ollama model | ✓ |
| 03 | Multilingual | `multilingual.spl` | Greet in any language — parametric `lang` demo | ✓ |
| 04 | Model Showdown | `showdown.spl` | Same prompt to multiple models via CTEs, compare output | ✓ |
| 05 | Self-Refine | `self_refine.spl` | Iterative improvement: draft → critique → refine loop | ✓ |
| 06 | ReAct Agent | `react_agent.spl` | Reasoning + Acting loop with tool-call pattern | ✓ |
| 07 | Safe Generation | `safe_generation.spl` | Exception handling for production LLM safety | ✓ |
| 08 | RAG Query | `rag_query.spl` | Retrieval-augmented generation over indexed documents | - |
| 09 | Chain of Thought | `chain.spl` | Multi-step reasoning: Research → Analyze → Summarize | ✓ |
| 10 | Batch Test | `batch_test.sh` | Automated testing of multiple .spl scripts across models | ✓ |

### Tier 2 — Agentic Patterns

| # | Recipe | Script | Description | Status |
|---|--------|--------|-------------|--------|
| 11 | Debate Arena | `debate.spl` | Adversarial debate between two LLM personas with a judge | ✓ |
| 12 | Plan and Execute | `plan_execute.spl` | Planner decomposes task into steps, executor runs each one | ✓ |
| 13 | Map-Reduce | `map_reduce.spl` | Split large docs into chunks, summarize each, combine results | - |
| 14 | Multi-Agent | `multi_agent.spl` | Researcher → Analyst → Writer collaboration via PROCEDURE | - |
| 15 | Code Review | `code_review.spl` | Multi-pass review: security, performance, style, bugs | ✓ |
| 16 | Reflection | `reflection.spl` | Meta-cognitive loop: solve → reflect → correct until confident | ✓ |
| 17 | Tree of Thought | `tree_of_thought.spl` | Explore multiple reasoning paths, score and pick the best | ✓ |
| 18 | Guardrails | `guardrails.spl` | Input/output safety pipeline with PII detection and filtering | ✓ |
| 19 | Memory Chat | `memory_chat.spl` | Persistent memory across conversations via memory.get/set | - |
| 20 | Ensemble Voting | `ensemble.spl` | Generate multiple answers, score and vote for consensus | ✓ |
| 21 | Multi-Model Pipeline | `multi_model.spl` | Per-step model selection with GENERATE...USING MODEL and quality loop | ✓ |
| 22 | Text2SPL Demo | `text2spl_demo.sh` | Natural language to SPL 2.0 compiler — prompt, workflow, and auto modes | - |

### Tier 3 — SPL Language Features (Completeness)

| # | Recipe | Script | Key Feature | Status |
|---|--------|--------|-------------|--------|
| 23 | Structured Output | `structured_output.spl` | `CREATE FUNCTION` with JSON schema — extract typed data from free text | ✓ |
| 24 | Few-Shot Prompting | `few_shot.spl` | Gold-standard examples embedded in `SELECT` context | ✓ |
| 25 | Nested Procedures | `nested_procs.spl` | `PROCEDURE` calling `PROCEDURE` — deep composability | ✓ |
| 26 | Prompt A/B Test | `ab_test.spl` | CTEs + `EVALUATE` scoring — compare two prompt variants, pick winner | ✓ |

### Tier 4 — Real-World Pipelines

| # | Recipe | Script | Domain | Status |
|---|--------|--------|--------|--------|
| 27 | Data Extraction | `data_extraction.spl` | Pull structured fields from messy text (names, dates, amounts) | ✓ |
| 28 | Customer Support Triage | `support_triage.spl` | Classify → route → draft response in one workflow | ✓ |
| 29 | Meeting Notes → Actions | `meeting_actions.spl` | Transcript in, structured TODO list + owners out | ✓ |
| 30 | Code Generator + Tests | `code_gen.spl` | Generate function, then generate its unit tests | ✓ |
| 31 | Sentiment Pipeline | `sentiment.spl` | Batch sentiment over a list, aggregate trends | ✓ |

### Tier 5 — Advanced Agentic Patterns

| # | Recipe | Script | Pattern | Status |
|---|--------|--------|---------|--------|
| 32 | Socratic Tutor | `socratic_tutor.spl` | Ask guiding questions rather than giving answers directly | ✓ |
| 33 | Interview Simulator | `interview_sim.spl` | Two-persona structured Q&A with evaluation | ✓ |
| 34 | Progressive Summarizer | `progressive_summary.spl` | Layered summary: sentence → paragraph → page | ✓ |
| 35 | Hypothesis Tester | `hypothesis.spl` | Generate hypothesis → design test → evaluate evidence | ✓ |

### Tier 6 — Tool Connectors (Multimodal)

Tool connectors mirror the LLM adapter pattern. `backend` is to connectors what `model` is to adapters.
Local and online backends are interchangeable — declared in `config.yaml` or overridden via `--connector`.

```yaml
# .spl/config.yaml
connectors:
  pdf:
    backend: pymupdf          # local default
    # backend: adobe-api      # online alternative
  transcribe:
    backend: whisper          # local
    model: base
    # backend: assemblyai     # online alternative
  tts:
    backend: piper            # local
    # backend: elevenlabs     # online alternative
```

```bash
# CLI override — same pattern as --adapter
spl2 run script.spl --connector pdf=pymupdf
spl2 run script.spl --connector transcribe=assemblyai
```

| # | Recipe | Script | Connector | Status |
|---|--------|--------|-----------|--------|
| 36 | PDF Analyst | `pdf_analyst.spl` | `tool.pdf_to_md` — ingest PDF, extract insights | todo |
| 37 | Audio → Action Items | `audio_actions.spl` | `tool.transcribe` — meeting recording → structured tasks | todo |


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
