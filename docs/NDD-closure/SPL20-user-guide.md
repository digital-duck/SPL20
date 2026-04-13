# SPL 2.0 User Guide

> Derived from the SPL 2.0 codebase — what you can actually do today.

---

## What Is SPL?

SPL (Structured Prompt Language) is an orchestration language for AI workflows.
You write workflows that mix LLM calls (`GENERATE`) with deterministic logic
(`CALL`, `WHILE`, `EVALUATE`). The language keeps these two modes explicit so
you always know where tokens are spent.

The mental model:

- `GENERATE` — ask an LLM. Costs tokens. Use for judgment, generation, ambiguity.
- `CALL` — run code. Zero tokens. Use for everything deterministic.

---

## Quick Start

### Install

```bash
pip install spl-llm
```

### Run a workflow

```bash
spl run my_workflow.spl --adapter ollama
spl run my_workflow.spl --adapter anthropic -p topic="climate change"
spl run my_workflow.spl --adapter openai -p doc="$(cat report.txt)"
```

### Pass a file as context

```bash
spl run my_workflow.spl --adapter ollama -d context=report.txt
spl run my_workflow.spl --adapter ollama -d slides=deck.pdf
```

`-d NAME=FILE` reads the file and injects it as the `NAME` parameter.
PDF files require `pip install dd-extract`.

---

## Supported Adapters

| Adapter | Notes |
|---------|-------|
| `ollama` | Local models — Llama, Gemma, Mistral, etc. |
| `anthropic` | Claude models via Anthropic API |
| `openai` | GPT models via OpenAI API |
| `azure_openai` | OpenAI on Azure |
| `google` | Gemini via Google AI Studio |
| `vertex` | Gemini on Vertex AI |
| `deepseek` | DeepSeek models |
| `qwen` | Qwen models |
| `openrouter` | Multi-provider routing |
| `bedrock` | AWS Bedrock (Claude, Titan) |
| `momagrid` | Distributed Momagrid runtime |
| `echo` | Returns input unchanged — use for testing |

---

## Workflow Structure

```spl
WORKFLOW name
    INPUT:
        @param1 TEXT,
        @param2 TEXT DEFAULT 'default_value'
    OUTPUT: @result TEXT
DO
    -- body statements
RETURN @result
EXCEPTION
    WHEN ExceptionType THEN
        -- handler statements
    WHEN OTHERS THEN
        -- catch-all
END
```

- `INPUT` parameters can have `DEFAULT` values.
- `OUTPUT` declares the variable returned to the caller.
- `RETURN` (or its deprecated alias `COMMIT`) finalises the workflow output.
  Use `RETURN @var WITH status = 'complete'` to attach metadata.
- `EXCEPTION` block is optional but recommended for production workflows.
- `WHEN OTHERS THEN` catches any unhandled exception type.

---

## Calling an LLM — GENERATE

```spl
-- Call a named function template
GENERATE summarize(@doc) INTO @summary

-- Override model for this call
GENERATE analyze(@text) USING MODEL 'gemma3' INTO @analysis
GENERATE analyze(@text) USING MODEL @model INTO @analysis

-- Control output length
GENERATE expand(@outline) WITH OUTPUT BUDGET 2000 TOKENS INTO @draft

-- Control temperature
GENERATE brainstorm(@topic) WITH TEMPERATURE 0.9 INTO @ideas

-- All options combined
GENERATE review(@code) WITH OUTPUT BUDGET 1024 TOKENS USING MODEL @model INTO @feedback

-- Discard output (side effects only, rare)
GENERATE log_event(@payload) INTO NONE
```

### Defining a function template

```spl
CREATE FUNCTION summarize(document TEXT)
RETURN TEXT
AS $$
Summarise the following document in 3 bullet points.

Document:
{document}
$$;
```

The `{param_name}` placeholder is replaced at runtime. The body becomes the
full prompt sent to the LLM.

### Pipe operator

Chain GENERATE calls — output of each step feeds the next:

```spl
GENERATE extract(@doc) | summarize() | translate('Spanish') INTO @result
```

Each `|` is a separate LLM call. Token cost is the sum of all segments.

---

## Deterministic Logic — CALL

```spl
-- Built-in function
CALL write_file(f'{@log_dir}/output.txt', @result) INTO NONE
CALL read_file('/data/context.txt') INTO @context

-- Python tool registered at runtime
CALL validate_json(@payload) INTO @is_valid

-- SPL PROCEDURE defined in the same file
CALL preprocess(@text) INTO @cleaned

-- Discard result
CALL send_alert(@message) INTO NONE
```

**CALL resolution order:** Python tool → built-in function → SPL PROCEDURE.
If none match, the runtime falls back to an LLM call with a warning.

### Built-in functions

**String:**
`len`, `upper`, `lower`, `truncate`

**List (JSON arrays internally):**
```spl
@items := []
@items := list_append(@items, @new_item)
@text  := list_concat(@items, '\n')      -- join to string
@n     := list_count(@items)
@item  := list_get(@items, 0)
```

**Map (JSON objects internally):**
```spl
@m := map()                              -- empty map
@m := map_set(@m, 'key', @value)
@v := map_get(@m, 'key', 'default')
@ok := map_has(@m, 'key')               -- returns 'true' or 'false'
@m := map_delete(@m, 'key')
@ks := map_keys(@m)                     -- returns JSON array
@vs := map_values(@m)
@m := map_merge(@m1, @m2)              -- later keys win
```

**File I/O:**
```spl
CALL write_file(@path, @content) INTO NONE
CALL read_file(@path) INTO @content     -- returns '' if file not found
```

### Registering Python tools

```python
from spl.tools import spl_tool

@spl_tool
def clean_text(text: str) -> str:
    return text.strip().replace("\n\n\n", "\n\n")
```

Or register at runtime:

```python
executor.register_tool("validate_json", my_fn)
```

---

## Branching — EVALUATE

```spl
EVALUATE @score
    WHEN > 0.8 THEN
        RETURN @result WITH status = 'high_confidence'
    WHEN > 0.5 THEN
        GENERATE improve(@result) INTO @result
        RETURN @result WITH status = 'refined'
    ELSE
        RETURN 'insufficient data' WITH status = 'failed'
END
```

### Condition types

| Syntax | Mode | Token cost |
|--------|------|------------|
| `WHEN > 0.8` | Numeric comparison (`>`, `<`, `>=`, `<=`, `=`, `!=`) | Zero |
| `WHEN = 'approved'` | String equality | Zero |
| `WHEN TRUE` / `WHEN FALSE` | Boolean check | Zero |
| `WHEN STARTSWITH 'err'` | String prefix check | Zero |
| `WHEN contains('CLOSED')` | Substring check | Zero |
| `WHEN ~ 'seems angry'` | Semantic / LLM-judged | LLM tokens |

All modes except `WHEN ~` are deterministic and cost zero tokens.
The `WHEN ~` semantic mode uses the adapter to evaluate the condition.

---

## Loops — WHILE

### Index-based

```spl
@i := 0
WHILE @i < @chunk_count DO
    CALL get_chunk(@doc, @i) INTO @chunk
    GENERATE summarize(@chunk) INTO @summary
    @summaries := list_append(@summaries, @summary)
    @i := @i + 1
END
```

### Semantic (LLM-judged condition)

```spl
WHILE 'the quality is not yet acceptable' DO
    GENERATE improve(@draft, @feedback) INTO @draft
    GENERATE evaluate(@draft) INTO @feedback
END
```

The runtime calls the LLM at each iteration to evaluate the condition string.
Use with caution — each iteration costs tokens. A safety cap of 100 iterations
is enforced by default; override via `max_iterations` in the WHILE clause
or the executor configuration.

---

## Exception Handling

```spl
EXCEPTION
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1 LIMIT 3
    WHEN ContextLengthExceeded THEN
        CALL truncate(@input, 4000) INTO @input
        GENERATE summarize(@input) INTO @result
        RETURN @result
    WHEN BudgetExceeded THEN
        RETURN @partial_result WITH status = 'partial'
    WHEN RefusalToAnswer THEN
        RETURN 'Request declined.' WITH status = 'refused'
    WHEN ModelOverloaded THEN
        RETURN '' WITH status = 'unavailable'
    WHEN OTHERS THEN
        LOGGING f'Unexpected error in workflow' LEVEL ERROR
        RETURN '' WITH status = 'error'
END
```

### Exception types

| Exception | Raised when |
|-----------|-------------|
| `HallucinationDetected` | Workflow explicitly calls `RAISE HallucinationDetected` |
| `RefusalToAnswer` | LLM declines to respond |
| `ContextLengthExceeded` | Input exceeds model context window |
| `BudgetExceeded` | LLM call count or token total hits the executor cap |
| `ModelOverloaded` | Model endpoint unavailable or rate-limited |
| `MaxIterationsReached` | WHILE loop hit the iteration limit |
| `QualityBelowThreshold` | Raised explicitly via `RAISE QualityBelowThreshold` |
| `NodeUnavailable` | Momagrid node unreachable |
| `ModelUnavailable` | Model not running / API key missing |
| `OTHERS` | Catch-all for any unmatched exception type |

Note: `ToolFailed` is mentioned in some documentation but is **not** registered
as an exception type. Errors in `CALL` tools propagate as Python exceptions,
not as `SPLWorkflowError` subclasses.

### RETRY

```spl
EXCEPTION
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1 LIMIT 3
END
```

`RETRY` re-executes the statement that raised the exception with the given
overrides. The default limit is 3 if `LIMIT` is omitted.
Exceeding the limit raises `MaxIterationsReached`.

---

## Variables and Types

### Assignment

```spl
@count := 0
@label := 'iteration ' || @count
@flag  := TRUE
@items := []
@data  := map()
```

### Types

| Type | Literals | Notes |
|------|----------|-------|
| `TEXT` | `'string'`, `$$...$$` | Default type |
| `NUMBER` | `42`, `3.14` | Numeric literals |
| `BOOL` | `TRUE`, `FALSE` | Use `WHEN TRUE` not `WHEN = TRUE` |
| `LIST` | `[]` | JSON array internally |
| `MAP` | `map()` | JSON object internally |

All variables are strings at runtime; type annotations on INPUT/OUTPUT are
documentation and parser hints.

### String operations

```spl
@msg := 'Hello, ' || @name || '!'          -- unambiguous concatenation
@n   := @count + 1                          -- numeric addition (falls back to concat)
@msg := f'Processing chunk {@i} of {@n}'   -- f-string interpolation
```

### Subscript assignment

```spl
@data['key'] := @value    -- works on MAP variables and STORAGE-typed variables
```

---

## Logging

```spl
LOGGING 'Workflow started' LEVEL INFO
LOGGING f'[Step {@step}] processing {@n} items' LEVEL DEBUG
LOGGING f'Low confidence: {@score}' LEVEL WARN
LOGGING f'Fatal: {@error}' LEVEL ERROR TO 'errors.log'
```

Log levels: `DEBUG < INFO < WARN < ERROR`. Default minimum output level: `INFO`.
`TO 'path'` appends to a file with ISO timestamp prefix instead of printing to console.
Debug messages are suppressed unless `--verbose` / `-v` is used.

---

## CLI Reference

```bash
# Run a workflow
spl run workflow.spl --adapter ollama
spl run workflow.spl --adapter anthropic -p param="value"
spl run workflow.spl -d context=document.txt
spl run workflow.spl --log-prompts ./prompt-logs/     # dump assembled prompts to files

# Validate syntax without running
spl validate workflow.spl

# Explain query plan (optimizer output)
spl explain workflow.spl

# Natural language to SPL
spl text2spl "summarize a PDF document" --adapter ollama

# Memory (persistent key-value store)
spl memory list
spl memory get  <key>
spl memory set  <key> <value>

# RAG — document search
spl doc-rag add   "document text here"
spl doc-rag query "what is the main topic" --top-k 5

# RAG — cookbook recipe search
spl code-rag import
spl code-rag query "judge-retry loop"

# Adapter info
spl adapters

# Config
spl config show
spl config set adapter ollama
```

### --log-prompts

Dumps every fully-assembled LLM prompt to a numbered `.md` file before
dispatch. Useful for debugging what the model actually receives.

---

## Prompt Caching

The executor has an optional prompt cache backed by the `.spl/memory.db`
SQLite store. When enabled, identical prompts (same model + same text) are
served from cache without an LLM call.

Configure via the Python API or config:

```python
executor = Executor(cache_enabled=True, cache_ttl=3600)
```

---

## Safety Caps

Two hard limits prevent runaway costs. Both raise `BudgetExceeded` when hit:

| Cap | Default | Meaning |
|-----|---------|---------|
| `max_llm_calls` | 25 | Max LLM calls per workflow execution |
| `max_total_tokens` | 100,000 | Max total tokens (input + output) per execution |

Adjust for long pipelines:

```bash
spl run workflow.spl --adapter ollama   # defaults apply
```

Or via the Python API:

```python
Executor(max_llm_calls=100, max_total_tokens=500_000)
```

---

## Memory — Persistent Storage

The `.spl/memory.db` SQLite database persists across runs.

```spl
-- Write from a workflow
STORE @result IN memory.last_result

-- Read in another workflow
@prev := memory.last_result
```

CLI equivalents: `spl memory get/set/list`.

---

## Debugging Tips

1. `--log-prompts ./logs` — see exactly what text reaches the model.
2. Add `LOGGING ... LEVEL DEBUG` statements; run with `spl run -v` to see them.
3. `CALL write_file(f'{@log_dir}/step.md', @var) INTO NONE` — snapshot any
   variable to a file for inspection after the run.
4. Use `--adapter echo` to dry-run a workflow without any LLM calls.
