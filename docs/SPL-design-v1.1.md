# SPL 2.0 Language Design — v1.2

> *"One beautiful language for Generative AI application development."*
> — Wen, 2026

---

## 0. The Name

**Structured Prompt Language** — and it stays that way.

During a late-night session on 2026-03-24, Wen noticed that SPL v2.0 had grown substantially: WHILE, EVALUATE, EXCEPTION, CALL, GENERATE, LOGGING, LIST, BOOL, f-strings — far beyond its origins as a prompt templating tool. The question arose: should the name be elevated to reflect this?

The answer is no. Here is why.

*"Structured Prompt Language"* is the right name — not despite what SPL has become, but because of it:

- **"Structured"** covers the full synthesis: declarative LLM invocation, procedural control flow, compositional piping. Structure is what makes SPL different from ad-hoc prompting.
- **"Prompt"** is honest about the primary execution target — a language model. As SPL grows to multimodal (IMAGE, AUDIO, VIDEO in v3.0), you still *prompt* image models, audio models, and video models. The word ages well.
- **Under-promise, over-deliver** is a better strategy than the reverse. SPL that calls itself a "Prompt Language" but ships with WHILE loops, EXCEPTION handlers, and a polyglot tool system is a pleasant surprise. A language that calls itself "Simple" becomes a punchline the moment any user hits a rough edge.

The principle: set expectations honestly, then exceed them. That is what SPL does.

> The three reviewers who gave critical feedback on v1.0 — Claude (Anthropic), Gemini (Google), and Z.ai — all independently flagged "Simple Programming Language" as a risk. Their concerns converged: unsearchable, generic, and eventually ironic as any successful language grows. We heard them.

---

## 1. Origin and Vision

SPL 2.0 was sparked by the same insight that made Oracle's PL/SQL enduring in enterprise data engineering: **a declarative language alone is not enough**. SQL is beautiful for expressing *what* you want — but the moment you need control flow, loops, error handling, or reusable logic, you need a procedural layer living *inside* the same language.

PL/SQL proved this in the relational era. SPL proves it in the Generative AI era.

*(Historical note: PL/SQL is cited as structural precedent — the insight that declarative + procedural in one language composes better than two separate languages. SPL borrows this architectural principle, not the baggage.)*

The observation: every modern AI application requires three layers of computation, today written in three separate languages:

| Layer | Purpose | Typical language |
|-------|---------|-----------------|
| **Data access** | Declare *what* to retrieve or invoke | SQL |
| **Control flow** | Express *how* to process it | Python |
| **Composition** | Chain and orchestrate operations | Bash |

Engineers context-switch constantly between these layers, marshalling data across string-escaping boundaries, maintaining incompatible type conventions, and writing glue code that owns no logic but breaks everything when it fails.

**SPL eliminates the glue code between these layers for the GenAI orchestration tier.** SPL is not a replacement for Python, SQL, or Bash — it is the composition layer that removes the stitching. You still write your tools in Python, your data queries in SQL. SPL is the language in which you express how they work together.

---

## 2. The Three-Language Synthesis

### The Core Claim

SPL is the *orchestration layer* that unifies how you express AI workflows — calling out to Python for computation, SQL for data, and composing it all without glue code:

```
SPL = SQL (declare what)  +  Python (control how)  +  Bash (compose and pipe)
```

Every AI application requires three things:

1. **Call an LLM** — declare *what* to ask, what context to provide, what format to expect. SQL taught us declarative expression. SPL's `GENERATE`, `SELECT`, `FROM`, `WHERE` come from that lineage.

2. **Process the result** — loops, conditionals, variables, error handling. Python taught us readable procedural code. SPL's `WHILE`, `EVALUATE`, `@var :=`, `EXCEPTION` come from there.

3. **Chain operations** — pipe outputs to inputs, redirect to files, compose steps. Bash taught us this. SPL's `|` operator, `@var` substitution style, and `LOGGING ... TO 'file'` come from there.

SPL does not eliminate Python, SQL, or Bash — it eliminates the stitching between them for the AI workflow tier. CALL tools are still written in Python. Data access still uses SQL. SPL is the score that tells all of them when and how to play.

### From SQL
- Declarative LLM invocation: `GENERATE`, `PROMPT`, `SELECT`, `FROM`, `WHERE`
- Set-based thinking: batch operations, CTEs (`WITH ... AS`)
- Transaction semantics: `COMMIT`, `ROLLBACK`
- Schema and typing: `INPUT @param TEXT`, `OUTPUT @result TEXT`
- `||` string concatenation (Oracle/PostgreSQL standard — unambiguous, unlike `+`)

### From Python
- Readable control flow: `WHILE`, `EVALUATE/WHEN/ELSE`
- Exception handling: `EXCEPTION WHEN HallucinationDetected THEN`
- Function definitions: `CREATE FUNCTION`, `CREATE PROCEDURE`
- Assignment: `@var := expr`
- F-string interpolation: `f'Chunk {@chunk_index} of {@chunk_count}'`
- Native types: `TEXT`, `NUMBER`, `BOOL`, `LIST`
- `LOGGING` — the `print()` of SPL, with log levels

### From Bash
- Pipe operator: `GENERATE extract(@doc) | summarize() | translate('Spanish') INTO @result`
- Redirection-style file output: `LOGGING @msg TO 'debug.log'`
- `@var` variable substitution style
- `$$...$$` here-docs for raw string bodies
- Script-like top-to-bottom execution model

---

## 3. Grammar Design Principles

### Principle 1: Minimum Orthogonal Constructs

Every keyword must add expressive power *not achievable* by existing constructs. If two constructs express the same computation, one must go.

**Applied:**
- No `IF/ELIF/ELSE` block — `EVALUATE/WHEN/ELSE` covers all boolean branching
- No `FOR` loop — `WHILE` with LIST-aware `IN` syntax covers both index-based and collection-based iteration (one keyword, two modes — same principle)
- No `CASE` expression — `EVALUATE` covers branching; f-strings cover inline formatting
- No `PRINT` — `LOGGING` covers all output needs (console + file + levels)

**On `WHILE` vs `FOR`:** SPL is not anti-FOR-loop — it is anti-unnecessary-keywords. `WHILE @i < @count` and `WHILE @item IN @items` are both `WHILE`. One keyword, two modes. That is what orthogonality means.

The test: *"Can I express this with what already exists?"* If yes, don't add a new keyword.

### Principle 2: Contextual Keywords (The Chinese Language Principle)

In Chinese, a single character can function as both noun and verb depending on context (e.g., 记录 = "record" as noun, "to record" as verb). SPL applies this deliberately:

- `EXCEPTION` — names the handler block AND implies "handle this exception"
- `LOGGING` — names the mechanism AND performs the action
- `COMMIT` — names the transaction concept AND performs the finalization

Fewer reserved words. Richer meaning per token.

### Principle 3: Readability by Design

A Python developer, a SQL analyst, and a DevOps engineer should each read any SPL workflow and find it immediately familiar. If all three groups can read the same code fluently — no context-switching required — the language has achieved its goal.

### Principle 4: ELSE not OTHERWISE

`ELSE` lives in every developer's muscle memory: Python's `else`, SQL's `CASE WHEN ... ELSE`, bash's `else`. SPL uses `ELSE`.

```spl
EVALUATE @score
    WHEN > 0.8 THEN
        COMMIT @result WITH status = 'high_confidence'
    ELSE
        GENERATE improve(@result) INTO @result
        COMMIT @result WITH status = 'refined'
END
```

---

## 4. The Efficient Runtime — SPL's Hallmark Feature

### The Golden Rule: Token Cost is Real

Every token spent on a deterministic operation is a token wasted — in latency, in dollars, and in unpredictability. Separating deterministic execution from probabilistic LLM calls is not an architectural nicety. **It is the primary mechanism for making AI applications efficient, predictable, and cost-effective.**

SPL makes the efficient choice the *natural* choice. The language steers you toward correctness.

### Dimension 1 — Deterministic vs Probabilistic

Every operation in an AI workflow belongs to exactly one category:

| Category | Characteristic | SPL keyword | Token cost |
|----------|---------------|-------------|------------|
| **Deterministic** | Logic can be expressed as code — precise, reproducible | `CALL` | Zero |
| **Probabilistic** | Requires judgment, generation, or ambiguity resolution | `GENERATE` | LLM tokens |

The author decides at write time. The runtime executes both seamlessly in the same workflow — no marshalling, no context switch, no glue code.

```spl
WHILE @chunk_index < @chunk_count DO
    CALL extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk   -- deterministic, 0 tokens
    GENERATE summarize_chunk(@chunk) INTO @chunk_summary                     -- probabilistic, costs tokens
    LOGGING f'[Chunk {@chunk_index}/{@chunk_count}] done' LEVEL DEBUG
    @summaries := list_append(@summaries, @chunk_summary)
    @chunk_index := @chunk_index + 1
END
```

### The Decision Rule

> *"If you can write it as code — write it as code. Reserve `GENERATE` for what only a language model can do."*

Clear logic + clear pattern → `CALL`. Ambiguity + judgment + generation → `GENERATE`.

### Dimension 2 — Polyglot Tools

The `--tools` mechanism is language-agnostic. The underlying contract is simple: a function that takes strings and returns a string. Any language can power a CALL.

| Language | Mechanism | Use case |
|----------|-----------|----------|
| **Python** | `@spl_tool` decorator | Data processing, NLP, APIs |
| **Rust** | FFI or subprocess | High-performance parsing, cryptography |
| **Go** | subprocess / gRPC | Concurrent I/O, network tools |
| **Java / JVM** | subprocess / gRPC | Enterprise systems, existing libraries |
| **JavaScript** | subprocess / Node.js | Web scraping, JSON manipulation |
| **Any binary** | subprocess | If it reads stdin and writes stdout, it works |

**Option: Inline UDF** for lightweight deterministic logic:
```spl
CREATE FUNCTION word_count(text TEXT) RETURNS NUMBER AS $$
    return str(len(text.split()))
$$;
```

**Option: Built-in functions** — shipped with zero configuration:
- `list_append`, `list_concat`, `list_count`, `list_get`
- `write_file`, `read_file`
- `len`, `upper`, `lower`, `truncate`

### Dimension 3 — Batch and Asynchronous by Design

SPL is designed for **batch and asynchronous workflows**. Streaming outputs are not supported — this is a deliberate architectural choice, not an oversight.

The reason: SPL is designed to run on Momagrid (Dimension 4), a globally distributed runtime where execution hops across compute nodes. Distributed dispatch introduces latency that makes streaming semantics impractical and potentially misleading. Owning the batch/async model explicitly produces more predictable, auditable workflows.

For real-time streaming use cases, SPL is the wrong tool. For agentic orchestration, multi-step reasoning, and batch AI pipelines, the batch model is the right one.

*(Note: the `STREAM` type planned for v4.0 refers to **data stream inputs** — sensor feeds, event queues, IoT data — ingested and processed as batches. It is not streaming LLM token output. The batch/async model holds throughout.)*

### Dimension 4 — Momagrid: Globally Distributed Execution

Momagrid is a globally distributed, decentralized runtime in which SPL workflows execute across a mesh of compute nodes — cloud, edge, and peer-to-peer. The SPL language itself does not change: a workflow written for local execution runs on Momagrid without modification.

| Without Momagrid | With Momagrid |
|-----------------|---------------|
| Single machine or single cloud | Global mesh of compute nodes |
| Centralized LLM API calls | Distributed LLM inference, closest node wins |
| CALL tools run locally | CALL tools dispatched to specialized nodes |
| Data moves to compute | Compute moves to data |
| Single point of failure | Decentralized, resilient by design |

*Full Momagrid architecture is documented separately. The key language-level contract: SPL workflows are location-transparent — the runtime handles dispatch, scheduling, and result aggregation without any change to the SPL source.*

---

## 5. Language Feature Reference

### 5.1 Workflow Structure

```spl
WORKFLOW name
    INPUT:
        @param1 TYPE,
        @param2 TYPE DEFAULT value
    OUTPUT: @result TYPE
DO
    -- body statements
RETURN @result
EXCEPTION
    WHEN ExceptionType THEN
        -- handler
    WHEN OTHERS THEN
        -- catch-all for any unmatched exception
END
```

Single-parameter workflows may keep INPUT on one line. For two or more parameters, put each on its own line.

**`RETURN` vs `COMMIT`:** `RETURN` is the canonical finalisation keyword. `COMMIT` is a deprecated alias accepted for backwards compatibility — prefer `RETURN` in all new workflows. Both accept `WITH status = '...'` metadata options:

```spl
RETURN @result WITH status = 'complete'
RETURN 'fallback' WITH status = 'degraded'
```

**`WHEN OTHERS THEN`** is a catch-all handler that matches any exception type not matched by an earlier `WHEN` clause. Use as the last handler in a production workflow.

### 5.2 LLM Invocation — GENERATE

```spl
GENERATE function_name(args) INTO @variable
GENERATE function_name(args) WITH TEMPERATURE 0.7 INTO @variable
GENERATE function_name(args) USING MODEL @model INTO @variable
```

Always costs LLM tokens. Use only when judgment or generation is required.

### 5.3 Deterministic Invocation — CALL

```spl
CALL tool_name(args) INTO @variable
CALL tool_name(args)
```

Zero tokens. Executes a registered tool (any language) or built-in function. Prefer `CALL` over `GENERATE` whenever the logic is deterministic.

### 5.4 Control Flow — EVALUATE

```spl
EVALUATE @expression
    WHEN > 0.8 THEN
        -- numeric comparison
    WHEN = 'approved' THEN
        -- string equality
    WHEN TRUE THEN
        -- boolean condition (preferred over WHEN = TRUE)
    WHEN STARTSWITH 'error' THEN
        -- string predicate
    ELSE
        -- default branch
END
```

**Evaluation modes:**

| Mode | Example | Token cost |
|------|---------|------------|
| Numeric comparison | `WHEN > 0.8` | Zero |
| String equality | `WHEN = 'approved'` | Zero |
| String predicate | `WHEN STARTSWITH 'err'` | Zero |
| Boolean | `WHEN TRUE` | Zero |
| Semantic *(v3.0 planned)* | `WHEN ~ 'is angry'` | LLM tokens |

All current EVALUATE modes are deterministic and cost zero tokens. Semantic evaluation (fuzzy matching, intent-based branching) is planned for v3.0 and will be a `GENERATE`-backed operation — token cost will be explicit.

### 5.5 Loops — WHILE

```spl
-- Index-based iteration
WHILE @i < @count DO
    ...
    @i := @i + 1
END

-- Collection-based iteration (LIST-aware)
-- @item is bound to each element in turn; @items must be a JSON array or comma-separated string
WHILE @item IN @items DO
    GENERATE process(@item) INTO @result
    @summaries := list_append(@summaries, @result)
END
```

One keyword, two iteration modes. No `FOR` needed — see Principle 1.

In the collection form, `@item` is automatically bound to each element of `@items` before the body executes. The collection is resolved at the start of the loop; modifications to `@items` inside the body do not affect the current iteration.

### 5.6 Exception Handling

```spl
EXCEPTION
    WHEN HallucinationDetected THEN
        RETRY WITH temperature = 0.1 LIMIT 3
    WHEN ContextLengthExceeded THEN
        -- handle oversized input
    WHEN BudgetExceeded THEN
        -- commit partial result
    WHEN RefusalToAnswer THEN
        -- handle LLM refusal
    WHEN ModelOverloaded THEN
        -- model unavailable
    WHEN ToolFailed THEN
        -- deterministic CALL threw
END
```

**Exception types:**

| Exception | Source | Meaning |
|-----------|--------|---------|
| `HallucinationDetected` | `RAISE` in workflow body | Raised explicitly by a validator tool or workflow logic when the generated output is deemed unreliable. There is no automatic confidence threshold — the workflow author decides when to raise it. |
| `ContextLengthExceeded` | GENERATE | Input exceeds the model's context window |
| `BudgetExceeded` | Runtime | LLM call count or token budget cap reached |
| `RefusalToAnswer` | GENERATE | LLM declined to respond |
| `ModelOverloaded` | GENERATE | Model endpoint unavailable or rate-limited |
| `ToolFailed` | CALL | Deterministic tool or built-in raised an exception — wraps the underlying Python error and makes it catchable in SPL |
| `MaxIterationsReached` | WHILE | Loop hit the iteration safety cap (default: 100) |
| `QualityBelowThreshold` | `RAISE` in workflow body | Raised explicitly when output quality does not meet a workflow-defined threshold |
| `OTHERS` | Any | Catch-all handler: matches any exception type not matched by an earlier `WHEN` clause |

**RETRY** accepts `LIMIT n` to prevent infinite loops. All production workflows should specify a limit:
```spl
RETRY WITH temperature = 0.1 LIMIT 3
```

Both `CALL` and `GENERATE` failures are caught by the same `EXCEPTION` block. `ToolFailed` distinguishes a CALL-side failure from a GENERATE-side failure.

**Pattern: explicit hallucination detection**

`HallucinationDetected` is raised by the workflow, not by the runtime automatically. The standard pattern is a CALL-based validator followed by a conditional raise:

```spl
GENERATE analyze(@doc) INTO @result
CALL validate_output(@result) INTO @is_valid
EVALUATE @is_valid
    WHEN = 'false' THEN
        RAISE HallucinationDetected 'validator rejected output'
END
```

### 5.7 LOGGING

```spl
LOGGING expr                              -- console, INFO level (default)
LOGGING expr LEVEL DEBUG                  -- suppressed at INFO minimum
LOGGING expr LEVEL WARN                   -- always shown
LOGGING expr LEVEL ERROR TO 'errors.log' -- file output with timestamp
LOGGING f'Chunk {@i} of {@n}: {@summary}' LEVEL INFO
```

Log levels: `DEBUG < INFO < WARN < ERROR`. Default minimum: `INFO`.

### 5.8 F-String Interpolation

```spl
@msg := f'Processing {@chunk_count} chunks with style={@style}'
LOGGING f'[Chunk {@chunk_index}/{@chunk_count}] score={@score}' LEVEL DEBUG
RETURN f'Done: {@chunk_count} chunks processed'
```

Use `{@varname}` inside `f'...'`. The `@` sigil is retained inside f-strings deliberately: it makes variable references unambiguous in templates that mix variable tokens with literal text, and it is consistent with the `@var` sigil used throughout SPL. Evaluated at runtime by substituting variable values.

### 5.9 String Concatenation — `||`

```spl
@label := '[Chunk ' || @i || '/' || @n || ']'
```

`||` is the unambiguous string concatenation operator (Oracle/PostgreSQL standard).
`+` remains supported but is ambiguous (also performs numeric addition).
**Prefer `||` for strings, `+` for numbers.**

### 5.10 BOOL Type

```spl
WORKFLOW check_doc
    INPUT:  @text TEXT, @strict BOOL DEFAULT FALSE
    OUTPUT: @passed BOOL
DO
    CALL has_pii(@text) INTO @passed         -- deterministic tool returns TRUE/FALSE

    EVALUATE @passed
        WHEN TRUE THEN
            LOGGING f'PII detected — strict={@strict}' LEVEL WARN
            COMMIT 'rejected' WITH passed = FALSE
        ELSE
            COMMIT 'approved' WITH passed = TRUE
    END
END
```

`TRUE` and `FALSE` are first-class literals. Preferred syntax: `WHEN TRUE` / `WHEN FALSE` — boolean variables evaluate naturally without `= TRUE`. The form `WHEN = TRUE` is also accepted but verbose. Prefer `BOOL` over `NUMBER` for flags and predicates: it signals intent explicitly.

### 5.11 Native LIST Type

```spl
@summaries := []                                  -- empty list
@summaries := list_append(@summaries, @item)      -- append
@text := list_concat(@summaries, '\n')            -- join to string
@n := list_count(@summaries)                      -- length
@item := list_get(@summaries, 0)                  -- index access
```

Lists are represented as JSON arrays internally. All list operations are deterministic built-ins — zero tokens.

### 5.12 Pipe Operator — `|`

```spl
GENERATE extract(@doc) | summarize() | translate('Spanish') INTO @result
```

Chains GENERATE steps: each step's output becomes the next step's input. Eliminates intermediate variables for linear pipelines. Inspired by Unix pipes and functional composition.

**Implemented in SPL v2.0.** Each pipe segment is a separate GENERATE call — the output of one becomes the input of the next. Context is not shared across pipe boundaries; each segment starts a fresh LLM call. Token cost is the sum of all segments.

### 5.13 Model Selection — `USING MODEL`

```spl
GENERATE approach(@problem) USING MODEL @model_a INTO @path_a
GENERATE analyze(@facts)    USING MODEL 'gemma3'  INTO @analysis
```

Overrides the default adapter model for a specific GENERATE call. Accepts a string literal or a variable. Used in multi-model workflows (e.g., tree-of-thought with per-path model diversity, model comparison pipelines).

---

## 6. Developer Experience

### Testing

SPL workflows can be tested by:
- Providing mock CALL tools (Python functions returning fixed strings) via `--tools`
- Setting `--adapter mock` for deterministic GENERATE responses in unit tests
- Using `LOGGING` statements at DEBUG level to trace intermediate state
- Writing per-agent/per-step outputs to `@log_dir` (pattern established in recipes 13–15)

A formal test harness and CALL mock protocol are on the v2.1 roadmap.

### Debugging

- `LOGGING ... LEVEL DEBUG` with `--log-level debug` surfaces all intermediate state
- Per-step file writes (`CALL write_file(...)`) create auditable snapshots
- Exception handlers with explicit status fields make failure mode visible in COMMIT output

### Tooling Roadmap

LSP (Language Server Protocol) support — syntax highlighting, inline type checking, CALL tool validation — is planned for v2.1. The grammar's orthogonality and small keyword set make LSP implementation tractable.

---

## 7. The Bigger Picture

SPL is a *composition layer* — the language in which you express the *orchestration* of AI workflows, calling out to deterministic Python tools where precision is needed and to LLMs where judgment is needed.

The analogy: just as a musical score is not the same as the instruments, SPL is not the compute itself — it is the notation that lets any developer write their own symphony and have it played by the AI orchestra. SQL became irreplaceable in the data era because once you wrote in SQL, everything *composed*. SPL's bet is the same for the GenAI era.

---

## 8. The Road Ahead

### SPL v2.0 — Where We Are Today

Text in, text out. Workflows that call LLMs, invoke deterministic tools, handle exceptions, run multi-agent pipelines, and execute on Momagrid. The foundation is solid: the grammar is orthogonal, the runtime is efficient, the language is readable by anyone.

### SPL v3.0 — Multimodal

When SPL v3.0 arrives, `INPUT` and `OUTPUT` will extend beyond `TEXT` to carry `IMAGE`, `AUDIO`, and `VIDEO` as first-class types. The language does not change. The keywords do not multiply.

```spl
-- v3.0: image understanding
WORKFLOW analyze_product_photo
    INPUT:  @photo IMAGE, @question TEXT
    OUTPUT: @answer TEXT
DO
    GENERATE describe_image(@photo) INTO @description
    GENERATE answer(@question, @description) INTO @answer
    RETURN @answer
END

-- v3.0: audio transcription pipeline
WORKFLOW meeting_to_actions
    INPUT:  @recording AUDIO, @attendees TEXT
    OUTPUT: @action_items TEXT
DO
    CALL transcribe(@recording) INTO @transcript        -- deterministic, 0 tokens
    GENERATE extract_actions(@transcript, @attendees) INTO @action_items
    COMMIT @action_items
END
```

### The Type Progression

| Version | Types | Era |
|---------|-------|-----|
| SPL v1.0 | `TEXT` | Prompt engineering |
| SPL v2.0 | `TEXT`, `NUMBER`, `BOOL`, `LIST` | Agentic workflows |
| SPL v3.0 | `TEXT`, `NUMBER`, `BOOL`, `LIST`, `IMAGE`, `AUDIO`, `VIDEO` | Multimodal AI |
| SPL v4.0 | + `STREAM`, `GRAPH`, `SENSOR` | Physical world integration (`STREAM` = data stream inputs, not LLM output streaming) |

In each version, the *language* stays structured and simple. The *world it can describe* grows larger. And the name — *Structured Prompt Language* — remains accurate: you are always structuring how you prompt intelligence, whatever form that intelligence takes.

---

## 9. Revision History

| Date | Version | Change |
|------|---------|--------|
| 2026-03-24 | v1.0 | Initial design document — Wen + Claude |
| 2026-03-24 | v1.0 | Added dualistic runtime section, OTHERWISE→ELSE, f-strings, LIST, `\|\|`, LOGGING levels |
| 2026-03-24 | v1.0 | Renamed "Dualistic" → "Efficient Runtime"; added polyglot tools dimension; added Momagrid as Dimension 4 |
| 2026-03-24 | v1.0 | Added "The Road Ahead" — SPL v3.0 multimodal vision (IMAGE, AUDIO, VIDEO types) |
| 2026-03-24 | v1.0 | Added BOOL type — TRUE/FALSE literals, type annotation, EVALUATE boolean conditions |
| 2026-03-24 | v1.0 | Added Section 0 (naming evolution); practical synthesis framing in Section 2 |
| 2026-03-25 | **v1.1** | **Reverted name to "Structured Prompt Language"** — based on unanimous critical feedback from The AI Quartet (Claude, Gemini, Z.ai); added Section 0 rationale for name staying |
| 2026-03-25 | **v1.1** | Reconciled "replaces three languages" (Sec 1) vs "composition layer" (Sec 6) — SPL eliminates glue code, not the languages themselves |
| 2026-03-25 | **v1.1** | Clarified EVALUATE modes table — numeric, string, boolean (zero tokens) vs semantic (v3.0, LLM tokens) |
| 2026-03-25 | **v1.1** | BOOL: preferred syntax changed to `WHEN TRUE` / `WHEN FALSE` (natural evaluation, not `= TRUE`) |
| 2026-03-25 | **v1.1** | Enumerated all exception types with source and meaning |
| 2026-03-25 | **v1.1** | RETRY LIMIT 3 established as production standard across all recipes |
| 2026-03-25 | **v1.1** | Pipe operator: marked as **implemented** in v2.0 (was "planned"); added context boundary note |
| 2026-03-25 | **v1.1** | Added `USING MODEL` as Section 5.13 (already in use in recipes 4, 10, 17, 21, 38–40) |
| 2026-03-25 | **v1.1** | Added batch/async design decision rationale (Dimension 3) — streaming not supported by design |
| 2026-03-25 | **v1.1** | Added Section 6 (Developer Experience) — testing, debugging, tooling roadmap |
| 2026-03-25 | **v1.1** | Momagrid: trimmed to summary in Dimension 4, full architecture in separate document |
| 2026-03-25 | **v1.1** | Clarified `STREAM` type (v4.0): data stream inputs (sensor/IoT/event queues), not LLM output streaming — batch/async model holds throughout |
| 2026-03-25 | **v1.1** | PL/SQL analogy: scoped to single historical reference, not recurring theme |
| 2026-03-25 | **v1.1** | `write_file`, `read_file` added to built-in functions list (already in use, now documented) |
| 2026-04-12 | **v1.2** | **NDD closure audit** — four gaps between spec and codebase identified and resolved |
| 2026-04-12 | **v1.2** | `RETURN` established as primary finalisation keyword; `COMMIT` documented as deprecated alias |
| 2026-04-12 | **v1.2** | `WHEN OTHERS THEN` catch-all documented in workflow structure and exception tables |
| 2026-04-12 | **v1.2** | `WHILE @item IN @items` — collection iteration variable binding documented; implementation fixed in executor |
| 2026-04-12 | **v1.2** | `ToolFailed` — exception registered in runtime; CALL tool errors now catchable via `WHEN ToolFailed THEN` |
| 2026-04-12 | **v1.2** | `HallucinationDetected` — corrected source: raised explicitly via `RAISE`, not by automatic confidence threshold; standard detection pattern documented |
| 2026-04-12 | **v1.2** | Exception table expanded: `MaxIterationsReached`, `QualityBelowThreshold`, `OTHERS` added |
