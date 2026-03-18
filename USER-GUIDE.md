# SPL 2.0 User Guide

This guide walks through installing, running, and writing SPL 2.0 programs.

---

## 1. Installation

```bash
# Create environment (conda or venv)
conda create -n spl python=3.11
conda activate spl

# Or with venv:
python -m venv .venv && source .venv/bin/activate

# Install SPL 2.0
cd SPL20
pip install -e ".[dev]"

# Verify installation
spl2 --help
pytest tests/   # should show 231 passed
```

### Optional Dependencies

```bash
# For OpenRouter, Ollama, or Momagrid adapters:
pip install httpx

# For RAG (vector search):
pip install numpy faiss-cpu

# For accurate OpenAI token counting:
pip install tiktoken
```

---

## 2. Your First SPL Program — Multilingual Hello World

The `examples/hello_world.spl` file demonstrates the core power of SPL 2.0:

```sql
-- SPL 2.0 Hello World (backward compatible with SPL 1.0)
PROMPT hello_world
WITH BUDGET 2000 tokens
USING MODEL gemma3

SELECT
    system_role("You are a friendly assistant. Respond in the language specified."),
    context.user_input AS input LIMIT 500 tokens,
    context.lang AS lang LIMIT 50 tokens

GENERATE
    greeting(input, lang)
WITH OUTPUT BUDGET 1000 tokens;
```

**5 lines of declarative SPL** — no Python boilerplate, no prompt template strings, no API client wiring. You declare *what* you want; the engine handles *how*.

### Parse and Validate

```bash
spl2 parse examples/hello_world.spl
```

Output:
```
Parsed OK: 1 statement(s)
  - Prompt: hello_world
```

### View Execution Plan

```bash
spl2 explain examples/hello_world.spl
```

This shows the token allocation, cost estimate, and step breakdown without making any LLM calls.

### Run with Echo Adapter (Testing)

```bash
spl2 run examples/hello_world.spl user_input="hello wen" lang="Chinese"
```

The `echo` adapter mirrors the prompt back — useful for verifying your query structure.

### Run with Real LLM

```bash
# Using local Ollama — multilingual greeting in 440ms:
ollama pull gemma3
spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"
```

Output:
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

**Same `.spl` file, any backend** — just swap the adapter:

```bash
# Chinese via Ollama (local, free)
spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="Chinese"

# French via Ollama
spl2 run examples/hello_world.spl --adapter ollama user_input="hello wen" lang="French"

# Japanese via OpenRouter (100+ cloud models)
export OPENROUTER_API_KEY="sk-or-..."
spl2 run examples/hello_world.spl --adapter openrouter user_input="hello wen" lang="Japanese"

# Via Claude Code CLI (subscription)
spl2 run examples/hello_world.spl --adapter claude_cli user_input="hello wen" lang="Spanish"

# Via Momagrid (decentralized GPU grid)
export MOMAGRID_HUB_URL="http://localhost:9000"
spl2 run examples/hello_world.spl --adapter momagrid user_input="hello wen" lang="Korean"
```

### Passing Parameters

Parameters can be passed two ways — both are equivalent:

```bash
# Explicit -p flag (traditional)
spl2 run query.spl -p user_input="hello" -p lang="French"

# Trailing KEY=VALUE (convenient shorthand)
spl2 run query.spl user_input="hello" lang="French"

# Mixed
spl2 run query.spl -p user_input="hello" lang="French"
```

### Create Your Own

Create a file `my_first.spl`:

```sql
PROMPT my_first
SELECT
    system_role('You are a helpful coding assistant') AS role,
    context.question AS question
GENERATE answer(question)
```

```bash
# Test with echo
spl2 run my_first.spl question="How do I reverse a list in Python?"

# Run with a real LLM
spl2 run my_first.spl --adapter ollama question="How do I reverse a list in Python?"
```

---

## 3. Ollama Proxy — General-Purpose LLM Query

The `examples/ollama_proxy.spl` script turns SPL 2.0 into a universal Ollama command-line wrapper:

```sql
PROMPT ollama_proxy
SELECT
    system_role('You are a helpful, knowledgeable assistant.'),
    context.prompt AS prompt
GENERATE answer(prompt)
```

### Basic Usage

```bash
# Query any Ollama model — swap models with --model (-m), no .spl edits needed:
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
Okay, let's break down quantum computing. It's a fascinating and complex field,
but here's an explanation designed to be understandable:

**What is Quantum Computing?**
Classical computers store and process information as bits. A bit can be either a
0 or a 1 — think of it like a light switch. Quantum computers, however, leverage
the principles of quantum mechanics...
============================================================
```

### The `--model` / `-m` Flag

The `--model` flag overrides `USING MODEL` in any `.spl` file at runtime — no source edits needed:

```bash
# Override model on any script:
spl2 run examples/hello_world.spl --adapter ollama --model gemma3 user_input="hello" lang="Chinese"
spl2 run examples/hello_world.spl --adapter ollama -m llama3.2 user_input="hello" lang="French"
spl2 run examples/hello_world.spl --adapter ollama -m mistral user_input="hello" lang="Spanish"
```

### Automated Ollama Model Testing

SPL 2.0 makes it trivial to benchmark and compare Ollama models:

```bash
# Test multiple models against the same prompt:
for model in gemma3 llama3.2 mistral phi3 qwen2.5; do
  echo "=== Testing $model ==="
  spl2 run examples/ollama_proxy.spl --adapter ollama -m $model prompt="What is 2+2?"
done
```

```bash
# Compare multilingual capability across models:
for model in gemma3 llama3.2 mistral; do
  echo "=== $model: Chinese ==="
  spl2 run examples/hello_world.spl --adapter ollama -m $model user_input="hello" lang="Chinese"
done
```

```bash
# Benchmark response quality with a harder prompt:
for model in gemma3 llama3.2 mistral phi3; do
  echo "=== $model ==="
  spl2 run examples/ollama_proxy.spl --adapter ollama -m $model \
    prompt="Explain the difference between concurrency and parallelism in 3 sentences"
done
```

The same patterns work with `--adapter openrouter` or `--adapter momagrid` — test cloud models or your decentralized grid with the exact same scripts.

---

## 4. SPL 1.0 Syntax — PROMPT Statements

PROMPT statements are single-shot LLM queries with structured context.

### Basic Structure

```sql
PROMPT <name>
[WITH BUDGET <n> TOKENS]
[USING MODEL '<model_name>']
SELECT
    <expression> [AS <alias>] [LIMIT <n> TOKENS],
    ...
[WHERE <condition>]
[ORDER BY <field> ASC|DESC]
GENERATE <function>(<args>) [WITH OUTPUT BUDGET <n> TOKENS]
                            [WITH TEMPERATURE <t>]
[STORE RESULT IN memory.<key>]
```

### Context Sources

| Source | Syntax | Description |
|--------|--------|-------------|
| System role | `system_role('description')` | Sets the system prompt |
| Parameter | `context.field_name` | Pulls from `--param` or runtime params |
| Memory | `memory.get('key')` | Reads from persistent SQLite store |
| RAG | `rag.query('search text', top_k=5)` | Semantic search over vector store |
| Function | `function_name(args)` | Calls user-defined function |

### Examples

**With token budget:**
```sql
PROMPT summarize_doc
WITH BUDGET 8000 TOKENS
USING MODEL 'claude-sonnet'
SELECT
    system_role('You are a precise summarizer'),
    context.document AS doc LIMIT 6000 TOKENS
GENERATE summarize(doc) WITH OUTPUT BUDGET 2000 TOKENS
```

**With memory and RAG:**
```sql
PROMPT answer_question
SELECT
    system_role('You are a knowledgeable assistant'),
    memory.get('user_preferences') AS prefs,
    rag.query('relevant background', top_k=3) AS context,
    context.question AS q
GENERATE answer(q)
```

**With result storage:**
```sql
PROMPT generate_summary
SELECT context.document AS doc
GENERATE summarize(doc)
STORE RESULT IN memory.last_summary
```

### User-Defined Functions

```sql
CREATE FUNCTION explain_code(code TEXT, language TEXT) RETURNS TEXT
AS $$
Explain the following {language} code in simple terms:

{code}

Provide a step-by-step breakdown.
$$

PROMPT explain
SELECT context.snippet AS code
GENERATE explain_code(code, 'Python')
```

### Common Table Expressions (CTEs)

Run sub-queries in parallel, then use their results:

```sql
WITH summary AS (
    PROMPT sub_summary
    SELECT context.document AS doc
    GENERATE summarize(doc)
)
PROMPT final_answer
SELECT
    summary AS background,
    context.question AS q
GENERATE answer(q)
```

---

## 5. SPL 2.0 Syntax — WORKFLOW Statements

WORKFLOW statements enable multi-step agentic patterns with control flow.

### Basic Structure

```sql
WORKFLOW <name>
  INPUT: @<var> <type>, ...
  OUTPUT: @<var> <type>
  [SECURITY: CLASSIFICATION: <level>]
  [ACCOUNTING: ...]
DO
  -- body statements
[EXCEPTION
  WHEN <ExceptionType> THEN
    -- handler statements]
END
```

### Variable Assignment

```sql
@name := 'value'
@count := 0
@combined := @first + @second
```

Variables are prefixed with `@` and hold string values.

### GENERATE INTO

Call the LLM and capture the result:

```sql
GENERATE summarize(@document) INTO @summary
GENERATE translate(@text, 'French') INTO @translated
```

### COMMIT

Finalize the workflow output:

```sql
COMMIT @result
COMMIT @result WITH status = 'complete', quality = @score
```

Execution stops after COMMIT. Only one COMMIT per execution path.

### EVALUATE (Branching)

Branch on conditions — either semantic (LLM-judged) or deterministic:

```sql
-- Semantic conditions (LLM evaluates)
EVALUATE @feedback
  WHEN 'positive' THEN
    @label := 'good'
  WHEN 'needs improvement' THEN
    GENERATE improve(@draft) INTO @draft
  OTHERWISE
    @label := 'neutral'
END

-- Deterministic conditions
EVALUATE @score
  WHEN > 0.8 THEN
    COMMIT @result WITH quality = 'high'
  WHEN > 0.5 THEN
    GENERATE refine(@result) INTO @result
  OTHERWISE
    RETRY
END
```

Semantic conditions (quoted strings like `'positive'`) use an LLM call to judge whether the value matches. Deterministic conditions (`> 0.8`, `< 5`) are evaluated numerically.

### WHILE (Loops)

```sql
@iteration := 0
WHILE @iteration < 5 DO
  GENERATE improve(@draft) INTO @draft
  @iteration := @iteration + 1
END
```

Loop terminates when the condition is false or after 100 iterations (safety limit).

### Exception Handling

```sql
DO
  GENERATE risky_task(@input) INTO @result
  COMMIT @result
EXCEPTION
  WHEN HallucinationDetected THEN
    @result := 'fallback value'
    COMMIT @result
  WHEN ModelOverloaded THEN
    RETRY
  WHEN OTHERS THEN
    RAISE HallucinationDetected 'unrecoverable'
END
```

**Available exception types:**

| Exception | When It Occurs |
|-----------|----------------|
| `HallucinationDetected` | LLM output fails fact-checking |
| `RefusalToAnswer` | LLM refuses the request |
| `ContextLengthExceeded` | Input exceeds model context window |
| `ModelOverloaded` | Provider rate limit or capacity error |
| `QualityBelowThreshold` | Output quality score too low |
| `MaxIterationsReached` | WHILE loop hit iteration limit |
| `BudgetExceeded` | Token budget exhausted |
| `NodeUnavailable` | Execution node unreachable |
| `OTHERS` | Catch-all for any exception |

### CALL (Sub-Procedures)

```sql
PROCEDURE validate_text(input_text TEXT) RETURNS TEXT
DO
  GENERATE check(@input_text) INTO @result
  COMMIT @result
END

WORKFLOW main
  INPUT: @data TEXT
  OUTPUT: @output TEXT
DO
  CALL validate_text(@data) INTO @output
  COMMIT @output
END
```

### RAISE

Explicitly trigger an exception:

```sql
RAISE HallucinationDetected 'confidence too low'
```

---

## 6. Agentic Patterns

### Pattern 1: Self-Refine

Iteratively improve output through critique:

```sql
WORKFLOW self_refine
  INPUT: @task text
  OUTPUT: @result text
DO
  GENERATE draft(@task) INTO @current
  @iteration := 0

  WHILE @iteration < 5 DO
    GENERATE critique(@current) INTO @feedback
    EVALUATE @feedback
      WHEN 'satisfactory' THEN
        COMMIT @current
      OTHERWISE
        GENERATE refined(@current, @feedback) INTO @current
        @iteration := @iteration + 1
    END
  END

  COMMIT @current WITH status = 'max_iterations'
END
```

Run it:
```bash
spl2 run examples/self_refine.spl --adapter claude_cli -p task="Write a haiku about coding"
```

### Pattern 2: ReAct Agent

Reasoning + Acting loop:

```sql
WORKFLOW react_agent
  INPUT: @task text
  OUTPUT: @answer text
DO
  @history := ''
  @iteration := 0

  WHILE @iteration < 10 DO
    GENERATE thought(@task, @history) INTO @current_thought
    GENERATE action_decision(@current_thought) INTO @action

    EVALUATE @action
      WHEN 'search' THEN
        CALL search_tool(@action) INTO @observation
      WHEN 'answer' THEN
        GENERATE final_answer(@history) INTO @answer
        COMMIT @answer
    END

    @history := @history + @current_thought
    @iteration := @iteration + 1
  END
EXCEPTION
  WHEN MaxIterationsReached THEN
    GENERATE best_answer(@history) INTO @answer
    COMMIT @answer WITH status = 'partial'
END
```

Run it:
```bash
spl2 run examples/react_agent.spl --adapter claude_cli -p task="What is the capital of France?"
```

### Pattern 3: Safe Generation

Exception handling for production safety:

```sql
WORKFLOW safe_generation
  INPUT: @prompt text
  OUTPUT: @result text
DO
  GENERATE response(@prompt) INTO @result
  GENERATE quality_score(@result) INTO @score

  EVALUATE @score
    WHEN > 0.8 THEN
      COMMIT @result WITH status = 'high_quality'
    OTHERWISE
      GENERATE improved(@result) INTO @result
      COMMIT @result WITH status = 'refined'
  END
EXCEPTION
  WHEN HallucinationDetected THEN
    GENERATE response(@prompt) INTO @result
    COMMIT @result WITH status = 'conservative'
  WHEN RefusalToAnswer THEN
    COMMIT @prompt WITH status = 'refused'
END
```

Run it:
```bash
spl2 run examples/safe_generation.spl --adapter claude_cli -p prompt="Explain quantum computing"
```

---

## 7. Prompt Caching

Enable caching to skip repeated LLM calls:

```bash
spl2 run my_query.spl --cache -p question="What is SPL?"
# First run: calls LLM, caches result
# Second run: returns cached result (0 tokens, 0 cost)
```

Cache is stored in `.spl/memory.db` (SQLite). Cache keys are SHA-256 hashes of the assembled prompt + model.

---

## 8. JSON Output and IR

### Parse to JSON AST

```bash
spl2 parse examples/self_refine.spl --json
```

Produces a portable JSON representation of the AST — useful for tooling, visualization, or cross-language interop.

### Programmatic Use

```python
import asyncio
from spl2 import parse, validate, optimize
from spl2 import Executor

# Parse
ast = parse(open("my_query.spl").read())

# Validate
analysis = validate(open("my_query.spl").read())

# Get execution plans
plans = optimize(open("my_query.spl").read())

# Execute
executor = Executor(adapter_name="echo")
results = asyncio.run(executor.execute_program(analysis, params={"key": "value"}))
for r in results:
    print(r.content)
executor.close()
```

---

## 9. text2SPL — Natural Language Compiler

Convert plain English to SPL 2.0 code:

```python
import asyncio
from spl2.text2spl import Text2SPL
from spl2.adapters.claude_cli import ClaudeCLIAdapter

compiler = Text2SPL(ClaudeCLIAdapter())

# Generate a PROMPT
code = asyncio.run(compiler.compile(
    "summarize a document with a 2000 token budget",
    mode="prompt"
))
print(code)

# Generate a WORKFLOW
code = asyncio.run(compiler.compile(
    "build an agent that iteratively refines an essay until quality > 0.8",
    mode="workflow"
))
print(code)

# Validate the output
valid, msg = Text2SPL.validate_output(code)
print(f"Valid: {valid}, Message: {msg}")
```

---

## 10. Adapter Setup Details

### Echo (Default)

No setup required. Returns the assembled prompt as the response. Useful for testing query structure.

```bash
spl2 run my_query.spl                    # echo is the default
spl2 run my_query.spl --adapter echo
```

### Claude CLI

Uses your existing Claude Code subscription (zero marginal cost).

```bash
# Prerequisites: Claude Code installed and authenticated
# https://docs.anthropic.com/en/docs/claude-code

spl2 run my_query.spl --adapter claude_cli
```

Notes:
- Automatically handles nested session detection
- Disables tool loading for faster startup
- 300s timeout per call (configurable in code)

### OpenRouter

Access 100+ models through a single API key.

```bash
pip install httpx
export OPENROUTER_API_KEY="sk-or-v1-..."

spl2 run my_query.spl --adapter openrouter
```

Models are specified in the `.spl` file via `USING MODEL`:
```sql
PROMPT my_query
USING MODEL 'anthropic/claude-sonnet-4-5'
SELECT ...
```

Available models include: `anthropic/claude-sonnet-4-5`, `openai/gpt-4o`, `google/gemini-2.0-flash`, `meta-llama/llama-3.1-70b-instruct`, and [many more](https://openrouter.ai/models).

### Ollama (Local)

Run models locally with zero cost.

```bash
pip install httpx

# Install and start Ollama
# https://ollama.ai/download
ollama pull llama3.2
ollama serve   # if not already running

spl2 run my_query.spl --adapter ollama
```

Supports any model installed via `ollama pull`: llama3.2, mistral, codellama, phi3, gemma2, qwen2.5-coder, etc.

For remote Ollama servers:
```bash
export OLLAMA_BASE_URL="http://192.168.1.10:11434"
spl2 run my_query.spl --adapter ollama
```

### Momagrid (Decentralized Grid)

Distribute inference across a decentralized GPU grid via [Momagrid](https://github.com/digital-duck/momagrid).

```bash
pip install httpx

# Start or connect to a Momagrid hub
export MOMAGRID_HUB_URL="http://localhost:9000"

spl2 run my_query.spl --adapter momagrid
```

Features:
- Hardware-aware routing (min compute tier, min VRAM)
- Automatic task dispatch to best available agent
- Hub-to-hub peering for multi-cluster execution
- Zero cost for local grid operators

Optional API key authentication:
```bash
export MOMAGRID_API_KEY="your-key"
spl2 run my_query.spl --adapter momagrid
```

### List All Adapters

```bash
$ spl2 adapters
Available LLM adapters (5):

  claude_cli     Wraps claude -p CLI (requires Claude Code installed)
  echo           Returns prompt as response (testing, no setup required)
  momagrid       Decentralized AI inference grid (requires httpx, MOMAGRID_HUB_URL)
  ollama         Local models via Ollama (requires httpx, ollama running)
  openrouter     100+ models via OpenRouter.ai (requires httpx, OPENROUTER_API_KEY)
```

---

## 11. RAG (Retrieval-Augmented Generation)

### Setup

```bash
pip install numpy faiss-cpu
```

### Indexing Documents (Programmatic)

```python
from spl2.storage.vector import VectorStore

store = VectorStore(".spl")

# Add documents
store.add("Python is a programming language", {"source": "wiki"})
store.add("JavaScript runs in browsers", {"source": "wiki"})
store.add_batch(
    ["Rust is fast", "Go has goroutines"],
    [{"source": "docs"}, {"source": "docs"}]
)

print(f"Indexed: {store.count()} documents")
store.close()
```

### Querying in SPL

```sql
PROMPT with_rag
SELECT
    rag.query('What language is best for systems programming?', top_k=3) AS context,
    context.question AS q
GENERATE answer(q)
```

The RAG results are automatically formatted and injected into the prompt context.

---

## 12. RAG via CLI

You can also manage the vector store directly from the command line:

```bash
# Add documents
spl2 rag add "Python is a programming language"
spl2 rag add "JavaScript runs in browsers"

# Check count
spl2 rag count

# Query
spl2 rag query "What language runs in browsers?" --top-k 3
```

---

## 13. Memory via CLI

Manage the persistent key-value store:

```bash
# Set a value
spl2 memory set user_name "Wen"
spl2 memory set preference "concise answers"

# Get a value
spl2 memory get user_name

# List all keys
spl2 memory list

# Delete
spl2 memory delete preference
```

Memory values are accessible in SPL via `memory.get('key')`:

```sql
PROMPT personalized
SELECT
    memory.get('user_name') AS name,
    context.question AS q
GENERATE answer(q)
```

---

## 14. Project Structure

```
SPL20/
  spl2/
    __init__.py          # Public API: parse(), validate(), optimize()
    tokens.py            # Token types (115 types)
    lexer.py             # Tokenizer
    parser.py            # Recursive descent parser
    ast_nodes.py         # AST node dataclasses
    analyzer.py          # Semantic validation
    optimizer.py         # Execution planning
    executor.py          # Runtime engine
    explain.py           # Plan rendering
    ir.py                # JSON serialization
    cli.py               # CLI (spl2 command)
    text2spl.py          # NL -> SPL compiler
    functions.py         # Function registry
    token_counter.py     # Model-aware token counting
    adapters/
      base.py            # LLMAdapter ABC
      echo.py            # Echo adapter (testing)
      claude_cli.py      # Claude Code CLI
      openrouter.py      # OpenRouter.ai
      ollama.py          # Local Ollama
      momagrid.py        # Decentralized Momagrid grid
    storage/
      memory.py          # SQLite key-value store
      vector.py          # FAISS vector store
  examples/
    hello_world.spl      # Multilingual greeting demo
    ollama_proxy.spl     # General-purpose LLM proxy / model tester
    self_refine.spl      # Iterative refinement pattern
    react_agent.spl      # ReAct agent pattern
    safe_generation.spl  # Exception handling pattern
  tests/                 # 231 tests across 13 test files
```

---

## 15. Type Reference

| Type | Description |
|------|-------------|
| `TEXT` | String / text content |
| `NUMBER` | Numeric value |
| `BOOLEAN` | True / False |
| `LIST` | Ordered collection |
| `JSON` | Structured data |

---

## 16. Troubleshooting

**`spl2: command not found`**
```bash
pip install -e .   # reinstall to register CLI entry point
```

**`Unknown adapter 'openrouter'`** or **`Unknown adapter 'momagrid'`**
```bash
pip install httpx  # required for openrouter, ollama, and momagrid
```

**`Claude CLI error (exit 1)`**
This usually means the Claude CLI can't run nested inside another Claude session. SPL 2.0 handles this automatically by stripping session markers, but ensure `claude` is in your PATH.

**`FAISS vector store requires numpy and faiss-cpu`**
```bash
pip install numpy faiss-cpu
```

**Parse error on keyword as variable name**
Keywords like `input`, `output`, `result`, `prompt` can be used as `@variable` names and function arguments. If you hit a parse error, check that the keyword isn't being used in an unsupported position.
