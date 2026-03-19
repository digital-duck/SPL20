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
$ spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"
============================================================
Model: gemma3
Tokens: 54 in / 21 out
Latency: 440ms
------------------------------------------------------------
你好，文！ (Nǐ hǎo, Wén!)

(Hello, Wen!)
============================================================
```

**Same `.spl` file, any backend** — swap `--adapter ollama` to `openrouter`, `claude_cli`, or `momagrid` without changing a single line of SPL code. That's the power of declarative.

## Quick Start

```bash
# Clone and install
git clone <repo-url> SPL20
cd SPL20
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (231 tests)
pytest tests/

# Try it out
spl2 parse   examples/hello_world.spl
spl2 explain examples/self_refine.spl
spl2 run     examples/hello_world.spl

# Run with a real LLM (Ollama)
pip install httpx
ollama pull gemma3
spl2 run examples/hello_world.spl --adapter ollama user_input="hello" lang="French"
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
spl2 run examples/hello_world.spl user_input="hello wen"

# Chinese via Ollama
spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"

# French via Ollama
spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="French"
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
spl2 run examples/ollama_proxy.spl --adapter ollama -m gemma3 prompt="Explain quantum computing"
spl2 run examples/ollama_proxy.spl --adapter ollama -m llama3.2 prompt="Write a haiku about coding"
spl2 run examples/ollama_proxy.spl --adapter ollama -m mistral prompt="What is 2+2?"
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
  spl2 run examples/ollama_proxy.spl --adapter ollama -m $model prompt="What is 2+2?"
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

## CLI

```bash
spl2 run      <file.spl> [--adapter NAME] [--model MODEL] [-p key=value | key=value ...]
spl2 execute  <file.spl> [--adapter NAME] [-m MODEL] [--cache] [key=value ...]
spl2 explain  <file.spl>              # Show execution plan (no LLM call)
spl2 parse    <file.spl> [--json]     # Validate syntax, optionally dump AST as JSON
spl2 validate <file.spl>              # Alias for parse
spl2 syntax   <file.spl>              # Alias for parse
spl2 text2spl "<description>" [--mode auto|prompt|workflow] [--adapter NAME] [-o FILE] [--execute]
spl2 compile  "<description>"          # Alias for text2spl
spl2 init                              # Initialise .spl/ workspace
spl2 adapters                          # List available LLM adapter engines
spl2 memory   {list,get,set,delete}    # Manage persistent memory store
spl2 rag      {add,query,count}        # Manage RAG vector store
spl2 version                           # Print version
```

### text2SPL Compiler

Compile natural language directly into SPL 2.0 code:

```bash
# Generate SPL from English
spl2 text2spl "summarize a document" --adapter ollama

# Save to file
spl2 text2spl "build a review agent" --mode workflow -o review.spl --adapter ollama

# Compile and execute in one step
spl2 compile "translate text to French" --execute --adapter anthropic text="Hello world"
```

Parameters can be passed with `-p KEY=VALUE` or as trailing `KEY=VALUE` arguments:
```bash
spl2 run query.spl -p question="What is SPL?"
spl2 run query.spl question="What is SPL?"          # same thing, shorter
spl2 run query.spl question="What is SPL?" lang=en   # multiple params
```

## LLM Adapters

SPL 2.0 supports 10 adapter backends — from local inference to major cloud providers:

```bash
$ spl2 adapters
Available LLM adapters (10):

  anthropic      Claude models via Anthropic API (requires anthropic, ANTHROPIC_API_KEY)
  claude_cli     Wraps claude -p CLI (requires Claude Code installed)
  deepseek       DeepSeek models (requires httpx, DEEPSEEK_API_KEY)
  echo           Returns prompt as response (testing, no setup required)
  google         Gemini models via Google GenAI (requires google-genai, GOOGLE_API_KEY)
  momagrid       Decentralized AI inference grid (requires httpx, MOMAGRID_HUB_URL)
  ollama         Local models via Ollama (requires httpx, ollama running)
  openai         GPT/o-series via OpenAI API (requires openai, OPENAI_API_KEY)
  openrouter     100+ models via OpenRouter.ai (requires httpx, OPENROUTER_API_KEY)
  qwen           Qwen models via DashScope (requires httpx, DASHSCOPE_API_KEY)
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
| `momagrid` | Decentralized AI inference grid | `pip install httpx`, set `MOMAGRID_HUB_URL` |

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
| Lexer | `spl2/lexer.py` | Tokenization (115 token types) |
| Parser | `spl2/parser.py` | Recursive descent parser |
| AST | `spl2/ast_nodes.py` | 30+ dataclass node types |
| Analyzer | `spl2/analyzer.py` | Semantic validation |
| Optimizer | `spl2/optimizer.py` | Token budget allocation, workflow planning |
| Executor | `spl2/executor.py` | Runtime execution engine |
| Explain | `spl2/explain.py` | ASCII plan rendering |
| IR | `spl2/ir.py` | JSON serialization of AST and plans |
| CLI | `spl2/cli.py` | Command-line interface |
| text2SPL | `spl2/text2spl.py` | Natural language to SPL compiler |
| Adapters | `spl2/adapters/` | LLM backend plugins (10 adapters) |
| Storage | `spl2/storage/` | SQLite memory + FAISS vector store |

## Requirements

- Python >= 3.11
- `click>=8.0` (CLI framework)
- Optional: `httpx` (for ollama/openrouter/momagrid/deepseek/qwen adapters)
- Optional: `anthropic` (for Anthropic adapter)
- Optional: `openai` (for OpenAI adapter)
- Optional: `google-genai` (for Google Gemini adapter)
- Optional: `numpy`, `faiss-cpu` (for RAG vector store)
- Optional: `tiktoken` (for accurate OpenAI token counting)

## License

Apache-2.0
