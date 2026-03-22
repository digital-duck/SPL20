# SPL 2.0: Structured Prompt Language

## What It Is

SPL 2.0 is a declarative language for orchestrating LLM-powered agentic workflows.
Where Python frameworks like LangGraph and AutoGen require imperative code to wire
together models, state machines, and error handlers, SPL 2.0 lets you describe
*what* a workflow should accomplish — not *how* to execute it.

The syntax draws from SQL. A `PROMPT` is the atomic unit, equivalent to a single
SELECT statement. A `WORKFLOW` is the procedural extension, equivalent to PL/SQL:
it adds variables, loops, branching, and exception handling around individual
prompts.

## Core Primitives

### SELECT / GENERATE

Every LLM interaction in SPL 2.0 has two sides:

- `SELECT` assembles the context flowing *into* the model: system roles, runtime
  parameters, retrieved documents, and memory.
- `GENERATE` invokes the model and captures what flows *out*.

```sql
PROMPT summarize_paper
SELECT
    system_role('You are a research analyst. Be concise and accurate.'),
    context.paper_text AS text
GENERATE summary(text)
```

### EVALUATE

`EVALUATE` enables branching where the condition can be either deterministic
(a numeric comparison) or semantic (an LLM judge). Detecting condition type is
automatic: quoted strings trigger an LLM judge call; numeric expressions evaluate
directly.

```sql
EVALUATE @quality_score
    WHEN > 0.8 THEN COMMIT @result WITH status = 'high_quality'
    WHEN > 0.5 THEN GENERATE improve(@result) INTO @result
    OTHERWISE RETRY WITH temperature = 0.1
END
```

### WHILE with Semantic Termination

`WHILE` loops can terminate on an LLM-judged quality condition rather than a
fixed counter. This enables genuine self-refinement: the loop runs until the
output is actually good, not just until it has run N times.

```sql
WHILE @iteration < 5 DO
    GENERATE critique(@draft) INTO @feedback
    EVALUATE @feedback
        WHEN 'satisfactory' THEN COMMIT @draft
        OTHERWISE
            GENERATE revise(@draft, @feedback) INTO @draft
            @iteration := @iteration + 1
    END
END
```

### EXCEPTION

SPL 2.0 provides a formal taxonomy of LLM-specific failure modes, each with
structured recovery:

| Exception | Trigger | Recovery |
|-----------|---------|----------|
| HallucinationDetected | Output fails fact check | Regenerate at lower temperature |
| RefusalToAnswer | Model declines request | Log and commit partial result |
| ContextLengthExceeded | Input too long | Compress context and retry |
| BudgetExceeded | Token limit reached | Commit best effort |
| QualityBelowThreshold | EVALUATE default | Retry with adjusted parameters |

## The Four-Layer Stack

```
┌─────────────────────────────────────────┐
│  Natural Language                        │  ← You describe what you want
├─────────────────────────────────────────┤
│  text2SPL compiler                       │  ← Translates to executable SPL
├─────────────────────────────────────────┤
│  SPL 2.0 (declarative specification)     │  ← The source file you write/edit
├─────────────────────────────────────────┤
│  Pluggable Runtime (adapters)            │  ← Executes on any backend
│  ├── ollama   (local GPU)               │
│  ├── openrouter (cloud, 100+ models)    │
│  ├── claude_cli (Anthropic)             │
│  └── momagrid (decentralized grid)      │
└─────────────────────────────────────────┘
```

The same `.spl` file runs on a local GPU, a cloud API, or a community-contributed
node on the Momagrid network — with no changes to the workflow logic.

## Why Declarative

Three structural advantages come from declaring intent rather than writing
imperative steps:

**Compiler optimization** — when the system understands the data flow between
steps, it can merge redundant LLM calls, parallelize independent branches, and
route each step to the most cost-effective model. An imperative framework hard-codes
execution order and cannot see these opportunities.

**Separation of concerns** — the workflow logic is independent of the runtime.
Switching from local Ollama to cloud OpenRouter is a one-flag change on the command
line, not a code rewrite.

**Accessibility** — the SQL-like syntax is familiar to analysts, data scientists,
and domain experts who understand their workflows but do not write Python framework
code. The barrier to writing a production agentic workflow should not be a
requirement to understand LangGraph state graphs.

## Cookbook Overview

The SPL 2.0 cookbook contains 35 recipes across 8 categories:

| Category | Examples |
|----------|---------|
| Basics | Hello World, Ollama Proxy, Multilingual, Model Showdown |
| Agentic | Self-Refine, ReAct Agent, Plan and Execute |
| Reasoning | Chain of Thought, Tree of Thought, Hypothesis Tester |
| Safety | Safe Generation, Guardrails Pipeline |
| Retrieval | RAG Query, Memory Conversation |
| Multi-Agent | Debate Arena, Multi-Agent Collaboration, Ensemble Voting |
| Application | Code Review, Sentiment Pipeline, Support Triage, Interview Sim |
| Benchmarking | Batch Test, Prompt A/B Test, Multi-Model Pipeline |

Each recipe is a self-contained `.spl` file with a `readme.md`, sample invocations,
and benchmark results from a run on a single GTX 1080 Ti using gemma3 via Ollama.
The full cookbook passes 100% of recipes on that hardware without modification.

## Getting Started

```bash
# Install
pip install spl-llm

# Run hello world
spl run cookbook/01_hello_world/hello.spl --adapter ollama

# Run with parameters
spl run cookbook/02_ollama_proxy/proxy.spl --adapter ollama \
    prompt="Explain quantum computing in one sentence"

# Compile natural language to SPL
spl text2spl "summarize a document and extract action items" \
    --adapter ollama --mode prompt
```

## Reference

- GitHub: github.com/digital-duck/spl-llm
- PyPI: pypi.org/project/spl-llm
- License: Apache 2.0
