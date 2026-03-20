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
# For OpenRouter, Ollama, Momagrid, DeepSeek, or Qwen adapters:
pip install httpx

# For Anthropic adapter:
pip install anthropic

# For OpenAI adapter:
pip install openai

# For Google Gemini adapter:
pip install google-genai

# For RAG (vector search):
pip install numpy faiss-cpu

# For Code-RAG (text2SPL example retrieval):
pip install chromadb onnxruntime

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

#### Per-Step Model Selection

Each GENERATE can target a specific model with `USING MODEL`:

```sql
-- Use a fast model for research, a reasoning model for analysis
GENERATE research(@topic) USING MODEL 'gemma3' INTO @facts;
GENERATE analyze(@facts) USING MODEL 'llama3.2' INTO @analysis;
GENERATE write_report(@analysis) USING MODEL 'mistral' INTO @report;
```

This enables multi-model pipelines where each step uses the optimal model for its task, without changing adapters.

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

Loop terminates when the condition is false or after 100 iterations (safety limit). Custom limits can be set per-loop via `max_iterations` in the AST.

#### Semantic WHILE Conditions

WHILE loops also support semantic (LLM-judged) conditions. The LLM receives all current `@variables` as context to make informed decisions:

```sql
WHILE 'the draft needs more detail' DO
  GENERATE expand(@draft) INTO @draft
END
```

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

Convert plain English to SPL 2.0 code via the CLI or Python API.

### Dedicated Compiler Adapter

text2SPL uses its own adapter and model, **separate from the runtime adapter** used by `spl2 run`. This lets you use a powerful code-generation model for compilation while keeping a different (e.g. faster or local) model for execution.

The recommended setup uses the `claude_cli` adapter with `claude-sonnet-4-6`, which runs against your Claude subscription (zero marginal cost, no VRAM required):

```bash
# No flags needed — picks up text2spl.adapter and text2spl.model from config
spl2 compile "summarize a document and store the result"
```

The config section that controls this (in `~/.spl/config.yaml`):

```yaml
text2spl:
  adapter: claude_cli          # dedicated compiler adapter
  model: claude-sonnet-4-6     # dedicated compiler model
  mode: auto
  validate: true
  max_retries: 2
```

To override the compiler adapter/model for a single call:
```bash
spl2 compile "..." --adapter ollama -m qwen2.5-coder   # benchmark another compiler
```

To switch the compiler globally:
```bash
spl2 config set text2spl.adapter ollama
spl2 config set text2spl.model qwen2.5-coder
```

### CLI Usage

```bash
# Compile (uses text2spl.adapter from config — claude_cli by default)
spl2 compile "summarize a document and store the result"

# Force a workflow
spl2 compile "build a review agent that refines until quality > 0.8" --mode workflow

# Save to file
spl2 compile "translate text to French" -o translate.spl

# Compile and execute in one step
spl2 compile "classify user intent" --execute text="Hello there"

# text2spl and compile are aliases for the same command
spl2 text2spl "summarize a document"
```

The compiler includes a **validate-and-retry loop** — if the generated code has syntax errors, the LLM automatically attempts to fix them (up to 2 retries at lower temperature).

### Modes

| Mode | Flag | Behavior |
|------|------|----------|
| Auto | `--mode auto` (default) | LLM decides between PROMPT or WORKFLOW |
| Prompt | `--mode prompt` | Forces a single PROMPT statement |
| Workflow | `--mode workflow` | Forces a WORKFLOW with control flow |

### Python API

```python
import asyncio
from spl2.text2spl import Text2SPL
from spl2.adapters import get_adapter

compiler = Text2SPL(get_adapter("claude_cli"))

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

## 10. Code-RAG — Self-Improving Example Retrieval for text2SPL

Code-RAG is a ChromaDB-backed vector store of `(description, SPL source)` pairs. When you run `spl2 compile`, it retrieves the most semantically similar SPL examples from the store and injects them into the compiler's context — replacing the handful of static hand-written examples with the full richness of your cookbook and any other pairs you have collected.

### Why Code-RAG

Without Code-RAG, the text2SPL compiler uses 4 fixed examples in its system prompt. This works for simple cases but misses patterns like multi-CTE fan-out, EVALUATE branching, PROCEDURE composition, or exception handling. With Code-RAG:

- **Better coverage** — every cookbook recipe (35+) is available as a retrieval target
- **Semantic matching** — if you ask for "a loop that refines until quality is high", the WHILE-quality-gate recipe is retrieved, not a generic summariser
- **Self-learning** — every successful `spl2 compile` call automatically adds its validated `(description, SPL)` pair back into the store, making the next compile better

### First-Time Setup

```bash
# Install dependency
pip install chromadb onnxruntime

# Prime the store with all cookbook recipes (run once)
spl2 code-rag import

# Verify
spl2 code-rag count
# → Code-RAG pairs indexed: 34
```

After this, every `spl2 compile` call automatically uses the store. You will see a status line on stderr:

```
Code-RAG: 34 examples indexed
```

### Commands

```bash
# Import cookbook recipes (initial priming)
spl2 code-rag import
spl2 code-rag import --cookbook-dir /path/to/cookbook

# Import additional pairs from a JSONL file
spl2 code-rag import --from ./my_pairs.jsonl
spl2 code-rag import --from ./research_pairs.jsonl --source synthetic --no-validate

# Add a single pair from a .spl file
spl2 code-rag add "classify a support ticket and route to the right team" ./route.spl

# Query — inspect what would be retrieved for a given description
spl2 code-rag query "summarize a long document into bullet points"
spl2 code-rag query "build an agent with quality loop" --top-k 5 --show-spl

# Count total pairs
spl2 code-rag count

# Export all pairs as JSONL (for fine-tuning or backup)
spl2 code-rag export
spl2 code-rag export --output ./my_backup.jsonl
```

### JSONL Import Format

Each line is a JSON object. The minimal required fields are `description` and either `spl_source` or `spl_file`:

```jsonl
{"description": "summarize a PDF", "spl_source": "PROMPT summarize_pdf\nSELECT ..."}
{"description": "route a support ticket", "spl_file": "./route.spl", "category": "agentic"}
{"description": "extract action items", "spl_source": "...", "name": "Action Extractor", "category": "application", "source": "research"}
# comment lines are skipped
```

Optional fields:

| Field | Description |
|-------|-------------|
| `name` | Human-readable name (shown in query results) |
| `category` | Recipe category (`basics`, `agentic`, `application`, etc.) |
| `source` | Provenance tag (`cookbook`, `user`, `synthetic`, `research`) |
| `spl_file` | Path to an external `.spl` file instead of inline `spl_source` |

The JSONL format is identical to `spl2 code-rag export` output — exported pairs can be re-imported into another project or after a DB reset.

### Validation on Import

By default, every pair in a JSONL import is validated through the SPL parser before being added. Invalid pairs are reported and skipped:

```
  line 3: invalid SPL (Parse error at 2:1: Expected PROMPT) — skipped
Imported 2 pair(s)  |  skipped 0  |  invalid 1
Total in store: 36
```

Use `--no-validate` to skip validation (e.g. when importing pairs already known to be valid, for speed):

```bash
spl2 code-rag import --from ./large_dataset.jsonl --no-validate
```

### Auto-Capture

When Code-RAG is enabled (the default), every `spl2 compile` invocation that produces valid SPL automatically adds the `(description, SPL)` pair to the store. The store grows as you use the compiler — no manual curation needed.

To disable auto-capture:
```bash
spl2 config set code_rag.auto_capture false
```

### Configuration

The `code_rag` section in `~/.spl/config.yaml`:

```yaml
code_rag:
  enabled: true            # set to false to disable Code-RAG entirely
  storage_dir: .spl/code_rag
  collection: spl_code_rag
  top_k: 4                 # number of examples retrieved per compile call
  auto_capture: true       # auto-add validated compile results to the store
```

### Self-Learning Flywheel

Code-RAG implements a continuous improvement loop:

```
Cookbook recipes
    +
User compile calls  ──► validated (description, SPL) pair
    +
JSONL imports                    │
                                 ▼
                        Code-RAG Vector DB
                                 │
                    ┌────────────┴───────────┐
                    ▼                        ▼
          Retrieval at compile time     Export JSONL
          (top-k injected into prompt)       │
                                             ▼
                                   Fine-tune dataset
                                   for specialty SPL model
```

Every new cookbook recipe and every user compile call automatically improves future code generation — with no manual labelling, because the SPL parser/analyzer is the oracle.

### Export for Fine-Tuning

When the store is large enough, export as a JSONL fine-tuning dataset:

```bash
spl2 code-rag export --output .spl/code_rag/training_data.jsonl
```

Each exported record:
```json
{"description": "summarize a document", "spl_source": "PROMPT ...", "name": "...", "category": "application", "source": "compile"}
```

This dataset is suitable for fine-tuning a code-specialised model (e.g. `qwen2.5-coder`) on SPL syntax — the long-term path to a dedicated SPL compiler model that no longer needs RAG at all.

---

## 11. Adapter Setup Details

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

### Anthropic (Claude)

Direct access to Claude models via the Anthropic API.

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

spl2 run my_query.spl --adapter anthropic
spl2 run my_query.spl --adapter anthropic -m claude-sonnet-4-20250514
```

Models: `claude-opus-4-0-20250514`, `claude-sonnet-4-20250514`, `claude-sonnet-4-5-20250514`, `claude-haiku-4-5-20251001`

### OpenAI

Direct access to GPT and o-series models.

```bash
pip install openai
export OPENAI_API_KEY="sk-..."

spl2 run my_query.spl --adapter openai
spl2 run my_query.spl --adapter openai -m gpt-4o
```

Models: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`, `o1`, `o3`, `o3-mini`

### Google (Gemini)

Direct access to Gemini models via Google GenAI SDK.

```bash
pip install google-genai
export GOOGLE_API_KEY="AI..."

spl2 run my_query.spl --adapter google
spl2 run my_query.spl --adapter google -m gemini-2.5-pro
```

Models: `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`

### DeepSeek

Access to DeepSeek chat and reasoning models.

```bash
pip install httpx
export DEEPSEEK_API_KEY="sk-..."

spl2 run my_query.spl --adapter deepseek
spl2 run my_query.spl --adapter deepseek -m deepseek-reasoner
```

Models: `deepseek-chat`, `deepseek-reasoner`

### Qwen (DashScope)

Access to Alibaba's Qwen models via DashScope.

```bash
pip install httpx
export DASHSCOPE_API_KEY="sk-..."

spl2 run my_query.spl --adapter qwen
spl2 run my_query.spl --adapter qwen -m qwen-max
```

Models: `qwen-max`, `qwen-plus`, `qwen-turbo`, `qwen-long`, `qwen2.5-72b-instruct`, `qwen2.5-coder-32b-instruct`

### List All Adapters

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

---

## 12. RAG (Retrieval-Augmented Generation)

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

## 13. RAG via CLI

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

## 14. Memory via CLI

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

## 15. Configuration (`spl2 config`)

SPL 2.0 stores configuration in `~/.spl/config.yaml`. This eliminates repetitive CLI flags — set your preferred adapter, model, and timeouts once, and every `spl2 run` inherits them automatically.

### Why Configuration Matters

- **Eliminates repetitive flags.** Instead of typing `--adapter ollama --model gemma3` on every command, set it once.
- **Per-adapter defaults are production-critical.** Each provider has different timeouts, model names, and endpoints. Config externalizes these knobs without touching code.
- **Reproducibility across environments.** Teams can share a `config.yaml` to ensure identical settings.

### Initialize

```bash
spl2 config init          # create ~/.spl/config.yaml with smart defaults
spl2 config init --force  # overwrite existing config with defaults
```

### View Configuration

```bash
spl2 config show          # show full config as YAML
spl2 config path          # show config and log directory paths
```

### Get Values

```bash
spl2 config get adapter                    # → echo
spl2 config get adapters.ollama.timeout    # → 120
spl2 config get adapters.ollama            # → shows all ollama settings
spl2 config get text2spl.mode              # → auto
```

### Set Values

Supports `KEY VALUE` pairs, `KEY=VALUE` syntax, and multiple settings at once:

```bash
# Single setting
spl2 config set adapter ollama
spl2 config set model gemma3

# Multiple settings at once
spl2 config set adapter ollama model gemma3

# KEY=VALUE syntax
spl2 config set adapter=ollama model=gemma3

# Dot-path for nested values
spl2 config set adapters.ollama.timeout 300
spl2 config set text2spl.mode workflow

# Boolean and numeric values auto-detected
spl2 config set cache true
spl2 config set log_console false
```

### Reset to Default

```bash
spl2 config reset adapter     # reset adapter to 'echo'
spl2 config reset log_level   # reset log_level to 'info'
```

### Smart Defaults

The default `~/.spl/config.yaml`:

```yaml
adapter: echo
model: ""
cache: false
storage_dir: .spl
log_level: info
log_console: false
text2spl:
  adapter: claude_cli        # dedicated compiler adapter (independent of spl2 run)
  model: claude-sonnet-4-6   # dedicated compiler model
  mode: auto
  validate: true
  max_retries: 2
code_rag:
  enabled: true              # use Code-RAG for text2SPL example retrieval
  storage_dir: .spl/code_rag
  collection: spl_code_rag
  top_k: 4                   # examples retrieved per compile call
  auto_capture: true         # auto-add validated compile results to store
adapters:
  ollama:
    base_url: http://localhost:11434
    default_model: llama3.2
    timeout: 120
  openrouter:
    default_model: anthropic/claude-sonnet-4-5
    timeout: 180
  anthropic:
    default_model: claude-sonnet-4-20250514
    timeout: 180
  openai:
    default_model: gpt-4o
    timeout: 180
  google:
    default_model: gemini-2.5-flash
    timeout: 180
  deepseek:
    default_model: deepseek-chat
    timeout: 180
  qwen:
    default_model: qwen-plus
    timeout: 180
```

### How Config Interacts with CLI Flags

CLI flags always override config values. The precedence order:

1. CLI flag (`--adapter ollama`) — highest priority
2. Config file (`~/.spl/config.yaml`)
3. Built-in defaults — lowest priority

```bash
# Config says adapter=ollama, but CLI overrides:
spl2 run query.spl --adapter echo    # uses echo, not ollama
```

---

## 16. Logging

Every `spl2 run` and `spl2 text2spl` command automatically writes a log file to `~/.spl/logs/`.

### Why Logging Matters

- **LLM calls are non-deterministic.** Unlike traditional code, you can't re-run and get the same result. Logs capture what adapter was called, what model responded, token counts, and latency — the forensic trail you need when output quality drops or costs spike.
- **Debugging multi-step workflows.** A WORKFLOW with WHILE loops, EVALUATE branches, and GENERATE steps can take dozens of LLM calls. The log file tells you *which step* diverged.
- **Cost tracking.** Token counts per run, per script, per adapter — all timestamped. Over time, these logs become your data source for understanding which workflows are expensive.

### Log File Location

```
~/.spl/logs/<script-name>-<adapter>-<YYYYMMDD-HHMMSS>.log
```

Example:
```
~/.spl/logs/hello-echo-20260318-231355.log
```

After every run, the log path is printed to stderr:
```
Log: /home/user/.spl/logs/hello-ollama-20260318-143022.log
```

### Log Content

```
14:30:22  INFO     spl2.cli  spl2 run hello.spl --adapter ollama
14:30:23  INFO     spl2.cli  Result: model=gemma3 tokens=75 latency=440ms
```

### Configuration

Control logging behavior via config:

```bash
# Set log verbosity: debug, info, warning, error
spl2 config set log_level debug

# Enable console output (logs to both file and terminal)
spl2 config set log_console true

# Check log directory
spl2 config path
```

### Viewing Logs

```bash
# List recent logs
ls -lt ~/.spl/logs/ | head

# View a specific log
cat ~/.spl/logs/hello-ollama-20260318-143022.log

# Search across logs
grep "ERROR" ~/.spl/logs/*.log
```

---

## 17. Project Structure

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
    config.py            # Configuration management (~/.spl/config.yaml)
    text2spl.py          # NL -> SPL compiler
    code_rag.py          # Code-RAG: ChromaDB store for (description, SPL) pairs
    functions.py         # Function registry
    token_counter.py     # Model-aware token counting
    adapters/
      base.py            # LLMAdapter ABC
      echo.py            # Echo adapter (testing)
      claude_cli.py      # Claude Code CLI
      openrouter.py      # OpenRouter.ai
      ollama.py          # Local Ollama
      momagrid.py        # Decentralized Momagrid grid
      anthropic.py       # Anthropic Claude API
      openai.py          # OpenAI API
      google.py          # Google Gemini API
      deepseek.py        # DeepSeek API
      qwen.py            # Alibaba DashScope API
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

## 18. Type Reference

| Type | Description |
|------|-------------|
| `TEXT` | String / text content |
| `NUMBER` | Numeric value |
| `BOOLEAN` | True / False |
| `LIST` | Ordered collection |
| `JSON` | Structured data |

---

## 19. Troubleshooting

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

**`Code-RAG: store empty — run spl2 code-rag import`**
Run `spl2 code-rag import` once to prime the store with cookbook recipes. After that, every `spl2 compile` call auto-captures pairs.

**`chromadb` or `onnxruntime` import errors**
```bash
pip install chromadb onnxruntime
```
If onnxruntime crashes with a NumPy version error, upgrade it:
```bash
pip install "onnxruntime>=1.18"
```

**`ANTHROPIC_API_KEY` billing concern with `claude_cli` adapter**
The `claude_cli` adapter strips `ANTHROPIC_API_KEY` and `ANTHROPIC_BASE_URL` from the subprocess environment before invoking `claude -p`, forcing use of your Claude subscription. It will never silently fall back to the paid API.

**Parse error on keyword as variable name**
Keywords like `input`, `output`, `result`, `prompt` can be used as `@variable` names and function arguments. If you hit a parse error, check that the keyword isn't being used in an unsupported position.
