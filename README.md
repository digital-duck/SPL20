# SPL 2.0 — Structured Prompt Language for Agentic Workflow Orchestration

SPL 2.0 extends the SQL-inspired [SPL 1.0](https://github.com/digital-duck/SPL) with declarative primitives for multi-step agentic workflows. Think of it as **PL/SQL for LLMs** — SPL 1.0 is the SQL (single queries), SPL 2.0 adds the PL (procedural control flow).

## What's New in 2.0

| Construct | Purpose |
|-----------|---------|
| `WORKFLOW ... DO ... END` | Multi-step agentic orchestration |
| `PROCEDURE ... DO ... END` | Reusable parameterized sub-workflows |
| `EVALUATE ... WHEN ... END` | LLM-judged (semantic) + deterministic branching |
| `WHILE ... DO ... END` | Iterative refinement loops |
| `GENERATE ... INTO @var` | LLM call with result capture |
| `GENERATE ... USING MODEL` | Per-step model selection in workflows |
| `@var := expr` | Variable assignment |
| `COMMIT @var` | Finalize workflow output |
| `DO ... EXCEPTION ... END` | LLM-specific error handling |
| `RAISE` / `RETRY` | Exception control flow |
| `CALL proc(args)` | Invoke sub-procedures |

Full backward compatibility with SPL 1.0 `PROMPT` statements is maintained.

## Why Declarative Beats Imperative

Most agentic frameworks (LangChain, CrewAI, AutoGen) require **hundreds of lines of imperative Python** to wire up prompts, manage context, handle errors, and switch between LLM providers. SPL 2.0 takes a radically different approach: **declare what you want, not how to get it.**

```sql
-- 5 lines of SPL replaces 100+ lines of Python
PROMPT hello_world
USING MODEL gemma3
SELECT
    system_role("You are a friendly assistant. Respond in the language specified."),
    context.user_input AS input,
    context.lang AS lang
GENERATE greeting(input, lang)
```

```bash
$ spl run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 440ms
------------------------------------------------------------
你好，文！ (Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
```

**Same `.spl` file, any backend** — swap `--adapter ollama` to `openrouter`, `claude_cli`, `bedrock`, `vertex`, `azure_openai`, or `momagrid` without changing a single line of SPL code. That's the power of declarative.

```bash
# Same recipe, three different backends — zero .spl changes
spl run examples/hello_world.spl --adapter ollama     -m llama3.2  user_input="hello" lang="French"
spl run examples/hello_world.spl --adapter anthropic  -m claude-sonnet-4-6  user_input="hello" lang="French"

export MOMAGRID_HUB_URL="<URL>"
spl run examples/hello_world.spl --adapter momagrid   -m llama3.2  user_input="hello" lang="French"
```

## Quick Start

```bash
# Clone and install
git clone https://github.com/digital-duck/SPL20.git
cd SPL20
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (231 tests)
pytest tests/

# Try it out
spl validate examples/hello_world.spl
spl explain  examples/self_refine.spl
spl run     examples/hello_world.spl

# Run with a real LLM (Ollama)
pip install httpx
ollama pull gemma3
spl run examples/hello_world.spl --adapter ollama user_input="hello" lang="French"
```

## Examples

**Hello World** — multilingual greeting in 5 lines:
```sql
PROMPT hello_world
USING MODEL gemma3
SELECT
    system_role("You are a friendly assistant. Respond in the language specified."),
    context.user_input AS input LIMIT 500 TOKENS,
    context.lang AS lang LIMIT 50 TOKENS
GENERATE greeting(input, lang)
```

```bash
# English (default echo adapter for testing)
spl run examples/hello_world.spl user_input="hello wen"

# Chinese via Ollama
spl run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"

# French via Ollama
spl run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="French"
```

**Ollama Proxy** — use any Ollama model as a general-purpose LLM in 4 lines:
```sql
PROMPT ollama_proxy
SELECT
    system_role('You are a helpful, knowledgeable assistant.'),
    context.prompt AS prompt
GENERATE answer(prompt)
```

```bash
# Swap models on the fly with --model (-m) — no .spl file edits needed:
spl run examples/ollama_proxy.spl --adapter ollama -m gemma3 prompt="Explain quantum computing"
spl run examples/ollama_proxy.spl --adapter ollama -m llama3.2 prompt="Write a haiku about coding"
spl run examples/ollama_proxy.spl --adapter ollama -m mistral prompt="What is 2+2?"
```

Output:
```
============================================================
Model: gemma3
Tokens: 44 in / 824 out
Latency: 12965ms
------------------------------------------------------------
Okay, let's break down quantum computing. It's a fascinating and complex field...
============================================================
```

**Automated Ollama model testing** — test any model with a single command:
```bash
# Test multiple models against the same prompt:
for model in gemma3 llama3.2 mistral phi3 qwen2.5; do
  echo "=== Testing $model ==="
  spl run examples/ollama_proxy.spl --adapter ollama -m $model prompt="What is 2+2?"
done
```

**Self-Refining Agent** (SPL 2.0):
```sql
WORKFLOW self_refine
  INPUT: @task text
  OUTPUT: @result text
DO
  GENERATE draft(@task) INTO @current

  WHILE @iteration < 5 DO
    GENERATE critique(@current) INTO @feedback
    EVALUATE @feedback
      WHEN 'satisfactory' THEN
        COMMIT @current
      OTHERWISE
        GENERATE refined(@current, @feedback) INTO @current
    END
  END

  COMMIT @current
EXCEPTION
  WHEN MaxIterationsReached THEN
    COMMIT @current WITH status = 'partial'
END
```

See `examples/` for more patterns (ReAct agent, safe generation with exception handling).

## Cookbook

48 ready-to-run recipes covering every major agentic pattern. Run the full suite against your Momagrid cluster or any adapter:

```bash
# Run all active recipes (45) against a local Ollama instance
python cookbook/run_all.py run --adapter ollama --model gemma3

# Run all active recipes in parallel across a 4-node Momagrid cluster
python cookbook/run_all.py run --adapter momagrid --model llama3.2 --workers 4

# Run a single recipe
spl run cookbook/41_human_steering/human_steering.spl \
    --tools cookbook/41_human_steering/tools.py \
    --adapter ollama topic="The future of decentralized AI inference"
```

### Basics

| ID | Recipe | Description |
|----|--------|-------------|
| 01 | Hello World | Minimal SPL program — verify adapter + model work |
| 02 | Ollama Proxy | General-purpose LLM query — proxy any Ollama model |
| 03 | Multilingual Greeting | Parametric context demo — greet in any language |
| 23 | Structured Output | `CREATE FUNCTION` with JSON schema — typed extraction from free text |
| 24 | Few-Shot Prompting | Gold-standard examples in `SELECT` context — in-context learning |

### Agentic & Control Flow

| ID | Recipe | Description |
|----|--------|-------------|
| 05 | Self-Refine | Iterative improvement: draft → critique → refine loop |
| 12 | Plan and Execute | Planner decomposes task; executor runs each step |
| 16 | Reflection Agent | Meta-cognitive loop: solve → reflect → correct until confident |
| 21 | Multi-Model Pipeline | Per-step model selection with `GENERATE … USING MODEL` |
| 25 | Nested Procedures | `PROCEDURE` calling `PROCEDURE` — deep composability |
| 36 | Tool-Use / Function-Call | Python functions as `CALL`-able tools — zero LLM cost |
| 41 ⭐ | Human Steering | Human-in-the-loop: pause for stdin feedback → conditional refinement |
| 43 ⭐ | Prompt Self-Tuning | Meta-programming: generate two prompt variants, A/B test, auto-select winner |
| 44 ⭐ | Adaptive Failover | Try primary model → quality gate → auto-failover to stronger model |

### Reasoning

| ID | Recipe | Description |
|----|--------|-------------|
| 09 | Chain of Thought | Multi-step: Research → Analyze → Summarize |
| 17 | Tree of Thought | Explore multiple reasoning paths, score and pick the best |
| 26 | Prompt A/B Test | CTEs + `EVALUATE` scoring — compare two prompt variants |
| 35 | Hypothesis Tester | Generate hypothesis → design test → evaluate evidence → conclude |

### Multi-Agent & Collaboration

| ID | Recipe | Description |
|----|--------|-------------|
| 04 | Model Showdown | Same prompt to multiple models — compare output and latency |
| 11 | Debate Arena | Adversarial debate between two LLM personas with a judge |
| 14 | Multi-Agent Collaboration | Researcher → Analyst → Writer via `PROCEDURE` |
| 20 | Ensemble Voting | Generate multiple answers, score and vote for consensus |
| 32 | Socratic Tutor | Ask guiding questions — persona-constrained generation |
| 33 | Interview Simulator | Two-persona structured Q&A with per-question scoring |

### Safety & Guardrails

| ID | Recipe | Description |
|----|--------|-------------|
| 07 | Safe Generation | Exception handling for production LLM safety |
| 18 | Guardrails Pipeline | Input/output safety pipeline with PII detection and filtering |

### Retrieval (RAG)

| ID | Recipe | Description |
|----|--------|-------------|
| 08 | RAG Query | Retrieval-augmented generation over indexed documents |
| 42 ⭐ | Knowledge Synthesis | RAG-writer: extract insights via LLM → persist to vector store |

### Application Patterns

| ID | Recipe | Description |
|----|--------|-------------|
| 13 | Map-Reduce Summarizer | Split large docs into chunks, summarize each, combine |
| 15 | Code Review | Multi-pass review: security, performance, style, bugs |
| 19 | Memory Conversation | Persistent memory across conversations |
| 22 | Text2SPL Demo | Natural language → SPL 2.0 compiler |
| 27 | Data Extraction | Pull structured fields from messy text |
| 28 | Customer Support Triage | Classify → route → draft response in one workflow |
| 29 | Meeting Notes to Actions | Transcript in, structured TODO list + owners out |
| 30 | Code Generator + Tests | Generate a function then generate its unit tests |
| 31 | Sentiment Pipeline | Batch sentiment over a list, aggregate trend statistics |
| 34 | Progressive Summarizer | Layered summary: sentence → paragraph → page |
| 37 | Headline News Aggregator | Generate → expand → evaluate coverage → daily digest |
| 45 ⭐ | Vision to Action | LLM classifies image description → deterministic action routing |
| 47 ⭐ | arXiv Morning Brief | Download PDFs → chunk → summarize → assemble Markdown brief |
| 48 ⭐ | Credit Risk Assessment | **Fin-service**: score gate → LLM risk review → APPROVED / MANUAL / REJECTED |
| 49 ⭐ | Regulatory News Audit | **Fin-service**: WHILE loop over news feed → compliance audit → CRITICAL ALERT on high risk |

### Cloud Provider Quickstarts *(adapter smoke tests, inactive by default)*

| ID | Recipe | Description |
|----|--------|-------------|
| 38 | Bedrock Quickstart | Fan out to Claude + Nova models on AWS Bedrock |
| 39 | Vertex AI Quickstart | Fan out to Gemini Pro / Flash / Lite on GCP Vertex AI |
| 40 | Azure OpenAI Quickstart | Fan out to GPT-4o / GPT-4o mini / GPT-3.5 on Azure |

> ⭐ = added in the 2026-04-05 release (recipes 41–45, 47–49)

### Benchmarking

| ID | Recipe | Description |
|----|--------|-------------|
| 10 | Batch Test | Automated testing of cookbook recipes across models |

## CLI

```bash
spl run      <file.spl> [--adapter NAME] [-m MODEL] [-p key=value | key=value ...]
             [--dataset NAME=FILE ...] [--resource FILE ...] [--tools FILE] [--cache]
spl validate <file.spl> [--json]     # Validate syntax, optionally dump AST as JSON
spl explain  <file.spl>              # Show execution plan (no LLM call)
spl text2spl "<description>" [--mode auto|prompt|workflow] [--adapter NAME] [-o FILE] [--execute]
spl adapters                          # List available LLM adapter engines
spl memory   {list,get,set,delete}    # Manage persistent memory store
spl doc-rag  {add,query,count}        # Manage RAG vector store (documents)
spl code-rag {import,query,count}     # Manage RAG vector store (SPL examples)
spl ui       [--port PORT] [--host HOST]  # Launch text2SPL Knowledge Studio
spl version                           # Print version
```

### text2SPL Compiler

Compile natural language directly into SPL 2.0 code:

```bash
# Generate SPL from English
spl text2spl "summarize a document" --adapter ollama

# Save to file
spl text2spl "build a review agent" --mode workflow -o review.spl --adapter ollama

# Compile and execute in one step
spl text2spl "translate text to French" --execute --adapter anthropic text="Hello world"
```

Parameters can be passed with `-p KEY=VALUE` or as trailing `KEY=VALUE` arguments:
```bash
spl run query.spl -p question="What is SPL?"
spl run query.spl question="What is SPL?"          # same thing, shorter
spl run query.spl question="What is SPL?" lang=en   # multiple params
```

## LLM Adapters

SPL 2.0 supports 13 adapter backends — from local inference to all three major cloud providers:

```bash
$ spl adapters
Available LLM adapters (13):

  anthropic      Claude models via Anthropic API (requires anthropic, ANTHROPIC_API_KEY)
  azure_openai   Azure OpenAI Service — GPT/o-series in your Azure subscription (requires openai, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY)
  bedrock        AWS Bedrock — Claude, Nova, Llama via Converse API (requires boto3, AWS credentials)
  claude_cli     Wraps claude -p CLI (requires Claude Code installed)
  deepseek       DeepSeek models (requires httpx, DEEPSEEK_API_KEY)
  echo           Returns prompt as response (testing, no setup required)
  google         Gemini models via Google GenAI (requires google-genai, GOOGLE_API_KEY)
  momagrid       Decentralized AI inference grid (requires httpx, MOMAGRID_HUB_URL)
  ollama         Local models via Ollama (requires httpx, ollama running)
  openai         GPT/o-series via OpenAI API (requires openai, OPENAI_API_KEY)
  openrouter     100+ models via OpenRouter.ai (requires httpx, OPENROUTER_API_KEY)
  qwen           Qwen models via DashScope (requires httpx, DASHSCOPE_API_KEY)
  vertex         GCP Vertex AI — Gemini models via ADC (requires google-genai, GOOGLE_CLOUD_PROJECT)
```

| Adapter | Description | Setup |
|---------|-------------|-------|
| `echo` | Returns prompt as response (testing) | Built-in, no setup |
| `claude_cli` | Wraps `claude -p` CLI (subscription) | Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code) |
| `ollama` | Local models via Ollama | `pip install httpx`, [install Ollama](https://ollama.ai) |
| `anthropic` | Claude models via Anthropic API | `pip install anthropic`, set `ANTHROPIC_API_KEY` |
| `openai` | GPT/o-series via OpenAI API | `pip install openai`, set `OPENAI_API_KEY` |
| `google` | Gemini models via Google GenAI | `pip install google-genai`, set `GOOGLE_API_KEY` |
| `deepseek` | DeepSeek chat & reasoning models | `pip install httpx`, set `DEEPSEEK_API_KEY` |
| `qwen` | Qwen models via Alibaba DashScope | `pip install httpx`, set `DASHSCOPE_API_KEY` |
| `openrouter` | 100+ models via OpenRouter.ai | `pip install httpx`, set `OPENROUTER_API_KEY` |
| `momagrid` | Decentralized AI inference grid (LAN or cloud) | `pip install httpx`, set `MOMAGRID_HUB_URL` |
| `bedrock` | **AWS** — Claude, Nova, Llama via Bedrock Converse API | `pip install boto3`, AWS credentials |
| `vertex` | **GCP** — Gemini models via Vertex AI | `pip install google-genai`, ADC + `GOOGLE_CLOUD_PROJECT` |
| `azure_openai` | **Azure** — GPT/o-series via Azure OpenAI Service | `pip install openai`, `AZURE_OPENAI_ENDPOINT` + key |

## Momagrid — Decentralized Grid Inference

The `momagrid` adapter routes SPL inference tasks to a [momagrid](https://github.com/digital-duck/momagrid) hub, which dispatches them across a LAN grid of GPU nodes. No `.spl` changes required — just switch the adapter.

### Setup

```bash
pip install httpx

# Point SPL at your hub (hub machine's LAN IP + port)
export MOMAGRID_HUB_URL=http://192.168.1.10:9000

# Or set it in ~/.igrid/config.yaml via the mg CLI:
# mg config --set hub.urls=http://192.168.1.10:9000
```

### Run a single recipe

```bash
spl run cookbook/01_hello_world/hello.spl --adapter momagrid -m llama3.2
```

### Run the cookbook — parallel mode for multi-agent load balancing

`run_all.py` uses Click subcommands. When `--adapter momagrid` is set, recipes are submitted **concurrently** so the hub dispatcher sees multiple tasks in the queue simultaneously and spreads work across all registered agents:

```bash
cd ~/projects/digital-duck/SPL20

# Run all active recipes in parallel on the momagrid hub
python cookbook/run_all.py run --adapter momagrid --model llama3.2

# Limit parallel workers (default: one per recipe)
python cookbook/run_all.py run --adapter momagrid --workers 4

# Run a subset of recipes in parallel
python cookbook/run_all.py run --adapter momagrid --ids 01-10,13

# List available recipes
python cookbook/run_all.py list
python cookbook/run_all.py list --category agentic

# Browse catalog
python cookbook/run_all.py catalog
python cookbook/run_all.py catalog --status new
```

> **Why parallel?** Sequential task submission (one at a time) means the dispatcher always sees a single task in the queue. With multiple equally-ranked agents (same tier, same load), the same agent wins every dispatch cycle — no distribution occurs. Parallel mode fills the queue so the load-balancer can spread tasks across all nodes.

## Architecture

```
.spl file
   |
   v
Lexer --> Parser --> Analyzer --> Optimizer --> Executor
(tokens)   (AST)    (validate)   (plan)       (run)
                                    |             |
                                    v             v
                                 Explain      LLM Adapter
                                 IR (JSON)    Memory Store
                                              Vector Store (RAG)
```

| Module | File | Purpose |
|--------|------|---------|
| Lexer | `spl/lexer.py` | Tokenization (115 token types) |
| Parser | `spl/parser.py` | Recursive descent parser |
| AST | `spl/ast_nodes.py` | 30+ dataclass node types |
| Analyzer | `spl/analyzer.py` | Semantic validation |
| Optimizer | `spl/optimizer.py` | Token budget allocation, workflow planning |
| Executor | `spl/executor.py` | Runtime execution engine |
| Explain | `spl/explain.py` | ASCII plan rendering |
| IR | `spl/ir.py` | JSON serialization of AST and plans |
| CLI | `spl/cli.py` | Command-line interface |
| text2SPL | `spl/text2spl.py` | Natural language to SPL compiler |
| Adapters | `spl/adapters/` | LLM backend plugins (13 adapters) |
| Storage | `spl/storage/` | SQLite memory + FAISS vector store |

## Requirements

- Python >= 3.11
- `click>=8.0` (CLI framework)
- Optional: `httpx` (for ollama/openrouter/momagrid/deepseek/qwen adapters)
- Optional: `anthropic` (for Anthropic adapter)
- Optional: `openai` (for OpenAI and Azure OpenAI adapters)
- Optional: `google-genai` (for Google Gemini and Vertex AI adapters)
- Optional: `boto3` (for AWS Bedrock adapter)
- Optional: `dd-vectordb[faiss]`, `dd-embed[sentence-transformers]` (for `spl doc-rag` vector store)
- Optional: `dd-vectordb[chroma]`, `dd-embed[sentence-transformers]` (for `spl code-rag` example store)
- Optional: `tiktoken` (for accurate OpenAI token counting)

## License

Apache-2.0
