# SPL 2.0 Language Design

> *"One beautiful language for Generative AI application development."*
> — Wen, 2026

---

## 0. The Name

SPL started as **Structured Prompt Language** — a fitting name for 2025, when everything was about prompts and prompt engineering.

Then something happened during a late-night session on 2026-03-24. Wen, reviewing the design, noticed: *"SPL v2.0 has WHILE, EVALUATE, EXCEPTION, CALL, GENERATE, LOGGING, LIST, BOOL, f-strings — this is not a prompt language anymore. This is a programming language."*

The rename took three seconds. Same acronym. Completely different identity.

**Simple Programming Language.**

The word *Simple* carries the entire philosophy:
- Simple to read — any SQL analyst, Python developer, or DevOps engineer can follow the code
- Simple to write — one language replaces three (SQL + Python + Bash)
- Simple to extend — the type system grows (TEXT → BOOL → LIST → IMAGE → AUDIO → VIDEO) without the grammar growing
- Simple to run — deterministic CALL and probabilistic GENERATE are the only two execution modes you ever need

The old name promised structure around prompts. The new name promises only one thing: **that expressing what you want should never be harder than the thing itself.**

That promise holds for v2.0 text workflows. It holds for v3.0 multimodal pipelines. It will hold for whatever comes after.

*A language named after a capability ages out the moment the capability expands. A language named after a virtue keeps it forever.*

---

## 1. Origin and Vision

SPL 2.0 was sparked by the same insight that made Oracle's PL/SQL the most enduring language in enterprise data engineering: **a declarative language alone is not enough**. SQL is beautiful for expressing *what* you want — but the moment you need control flow, loops, error handling, or reusable logic, you need a procedural layer living *inside* the same language.

PL/SQL proved this in the relational era. SPL proves it in the Generative AI era.

The observation: every modern AI application requires three layers of computation, today written in three separate languages:

| Layer | Purpose | Typical language |
|-------|---------|-----------------|
| **Data access** | Declare *what* to retrieve or invoke | SQL |
| **Control flow** | Express *how* to process it | Python |
| **Composition** | Chain and orchestrate operations | Bash |

Engineers context-switch constantly between these layers, marshalling data across string escaping boundaries, maintaining incompatible type conventions, and writing glue code that owns no logic but breaks everything when it fails.

**SPL eliminates that entirely for the GenAI layer.** One language. One runtime. No glue.

---

## 2. The Three-Language Synthesis

### The Practical Version

Every AI application you will ever build requires three things:

1. **Call an LLM** — you need to declare *what* to ask, what context to provide, what format to expect. SQL taught us how to do this declaratively. SPL's `GENERATE`, `SELECT`, `FROM`, `WHERE` come directly from that lineage.

2. **Process the result** — you need loops, conditionals, variables, error handling. Python taught us how to do this readably. SPL's `WHILE`, `EVALUATE`, `@var :=`, `EXCEPTION` come from there.

3. **Chain operations together** — you need to pipe outputs to inputs, redirect to files, compose steps. Bash taught us this. SPL's `|` operator, `@var` substitution style, and `LOGGING ... TO 'file'` come from there.

Today, you write these three layers in three separate languages. You context-switch constantly. You write glue code. You debug across runtime boundaries.

**SPL collapses all three into one.** Not by inventing new concepts, but by taking what already works in each language, discarding what doesn't, and adding only what's missing for the GenAI era.

### The Synthesis

SPL deliberately borrows the *best* of each language — and nothing else.

```
SPL = SQL (declare what)  +  Python (control how)  +  Bash (compose and pipe)
```

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
- Native types: `TEXT`, `NUMBER`, `LIST`
- `LOGGING` — the `print()` of SPL, with log levels

### From Bash
- Pipe operator: `GENERATE extract(@doc) | summarize() INTO @result`
- Redirection-style file output: `LOGGING @msg TO 'debug.log'`
- `@var` variable substitution style
- `$$...$$` here-docs for raw string bodies
- Script-like top-to-bottom execution model

---

## 3. Grammar Design Principles

### Principle 1: Minimum Orthogonal Constructs

Every keyword must add expressive power *not achievable* by existing constructs. If two constructs express the same computation, one must go.

**Applied:**
- No `IF/ELIF/ELSE` block — `EVALUATE/WHEN/ELSE` already covers all boolean branching
- No `FOR` loop — `WHILE` with LIST-aware syntax covers all iteration
- No `CASE` expression — `EVALUATE` covers branching; f-strings cover inline formatting
- No `PRINT` — `LOGGING` covers all output needs (console + file + levels)

The test: *"Can I express this with what already exists?"* If yes, don't add a new keyword.

### Principle 2: Contextual Keywords (The Chinese Language Principle)

In Chinese, a single character can function as both noun and verb depending on context (e.g., 记录 = "record" as noun, "to record" as verb). This reduces vocabulary while increasing expressiveness.

SPL applies this deliberately:
- `EXCEPTION` — names the handler block AND implies "handle this exception"
- `LOGGING` — names the mechanism AND performs the action (active, not passive)
- `COMMIT` — names the transaction concept AND performs the finalization

Fewer reserved words. Richer meaning per token.

### Principle 3: Readability by Design


A Python developer, a SQL analyst, and a DevOps engineer should each read any SPL workflow and find it immediately familiar. If all three groups can read the same code fluently — no context-switching required — the language has achieved its goal.

### Principle 4: ELSE not OTHERWISE

`ELSE` lives in every developer's muscle memory: Python's `else`, SQL's `CASE WHEN ... ELSE`, bash's `else`. `OTHERWISE` is verbose and alien. SPL uses `ELSE`.

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

This is the most important design decision in SPL, and the direct analogue of what made PL/SQL successful.

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

Consider `chunk_plan(@document)`: counting words, estimating tokens, deciding boundaries. Pure computation. No judgment needed. **CALL it. Zero tokens.**

Consider `summarize_chunk(@chunk)`: language understanding, compression, judgment. **GENERATE it.**

```spl
WHILE @chunk_index < @chunk_count DO
    CALL extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk   -- deterministic, 0 tokens
    GENERATE summarize_chunk(@chunk) INTO @chunk_summary                     -- probabilistic, costs tokens
    LOGGING f'[Chunk {@chunk_index}/{@chunk_count}] done' LEVEL DEBUG
    @summaries := list_append(@summaries, @chunk_summary)
    @chunk_index := @chunk_index + 1
END
```

Same workflow. Two execution models. One language. Token cost concentrated exactly where intelligence is genuinely needed.

### Dimension 2 — Polyglot Tools

The `--tools` mechanism is language-agnostic by design. The `@spl_tool` decorator is a Python convenience, but the underlying contract is simple: a function that takes strings and returns a string. Any language that can expose that interface can power a CALL.

| Language | Mechanism | Use case |
|----------|-----------|----------|
| **Python** | `@spl_tool` decorator | Data processing, NLP, APIs |
| **Rust** | FFI or subprocess | High-performance parsing, cryptography |
| **Go** | subprocess / gRPC | Concurrent I/O, network tools |
| **Java / JVM** | subprocess / gRPC | Enterprise systems, existing libraries |
| **JavaScript** | subprocess / Node.js | Web scraping, JSON manipulation |
| **Any binary** | subprocess | If it reads stdin and writes stdout, it works |

This means existing enterprise logic written in any language becomes a first-class `CALL`-able tool in SPL — without rewriting it in Python and without spending a single LLM token on it.

```bash
# Python tools
spl run workflow.spl --tools tools/chunk_tools.py

# Rust tool via gRPC (future)
spl run workflow.spl --tools tools/fast_tokenizer.rs.json
```

**Option: Inline UDF** for lightweight deterministic logic:
```spl
CREATE FUNCTION word_count(text TEXT) RETURNS NUMBER AS $$
    return str(len(text.split()))
$$;
```

**Option: Built-in functions** — shipped with zero configuration:
- `list_append`, `list_concat`, `list_count`, `list_get`
- `len`, `upper`, `lower`, `truncate`

### Dimension 3 — The Decision Rule

> *"If you can write it as code — write it as code. Reserve `GENERATE` for what only a language model can do."*

Clear logic + clear pattern → `CALL`. Ambiguity + judgment + generation → `GENERATE`.

This discipline produces workflows that are fast where speed is possible, intelligent where intelligence is required, and auditable throughout.

### Dimension 4 — Momagrid: Globally Distributed and Decentralized Execution

The three dimensions above describe *what* runs and *how*. Momagrid answers *where*.

Momagrid is a globally distributed, decentralized runtime in which SPL workflows can execute across a mesh of compute nodes — cloud, edge, and peer-to-peer. Rather than a single machine or a centralized cloud, Momagrid treats the world's compute as a shared resource, routing workflow steps to wherever execution is cheapest, fastest, or most private.

For SPL, Momagrid changes the execution model fundamentally:

| Without Momagrid | With Momagrid |
|-----------------|---------------|
| Single machine or single cloud | Global mesh of compute nodes |
| Centralized LLM API calls | Distributed LLM inference, closest node wins |
| CALL tools run locally | CALL tools can be dispatched to specialized nodes |
| Data moves to compute | Compute moves to data |
| Single point of failure | Decentralized, resilient by design |

The SPL language itself does not change. A workflow written for local execution runs on Momagrid without modification — the runtime handles dispatch, scheduling, and result aggregation. The `ON GRID` clause in SPL 1.0 was the first surface of this idea; Momagrid is its full realization.

This is what makes SPL unique among AI workflow languages: it is not tied to any single cloud, any single LLM provider, or any single machine. It is a language for a decentralized intelligence layer — **the score that any orchestra, anywhere in the world, can play**.

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
EXCEPTION
    WHEN ExceptionType THEN
        -- handler
END
```

Single-parameter workflows may keep INPUT on one line. For two or more parameters, put each on its own line — readability scales with parameter count.

### 5.2 LLM Invocation — GENERATE

```spl
GENERATE function_name(args) INTO @variable
GENERATE function_name(args) WITH TEMPERATURE 0.7 INTO @variable
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
        -- high branch
    WHEN > 0.5 THEN
        -- medium branch
    ELSE
        -- default branch
END
```
Covers all IF/ELIF/ELSE needs. Works with numeric comparisons, string equality, and semantic conditions.

### 5.5 Loops — WHILE

```spl
-- Index-based
WHILE @i < @count DO
    ...
    @i := @i + 1
END

-- List iteration (LIST-aware extension)
WHILE @item IN @items DO
    ...
END
```

### 5.6 LOGGING

```spl
LOGGING expr                              -- console, INFO level (default)
LOGGING expr LEVEL DEBUG                  -- suppressed at INFO minimum
LOGGING expr LEVEL WARN                   -- always shown
LOGGING expr LEVEL ERROR TO 'errors.log' -- file output with timestamp
LOGGING f'Chunk {@i} of {@n}: {@summary}' LEVEL INFO
```

Log levels: `DEBUG < INFO < WARN < ERROR`. Default minimum: `INFO`.

### 5.7 F-String Interpolation

```spl
@msg := f'Processing {@chunk_count} chunks with style={@style}'
LOGGING f'[Chunk {@chunk_index}/{@chunk_count}] score={@score}' LEVEL DEBUG
COMMIT f'Done: {@chunk_count} chunks processed'
```

Use `{@varname}` inside `f'...'`. Evaluated at runtime by substituting variable values.

### 5.8 String Concatenation — `||`

```spl
@label := '[Chunk ' || @i || '/' || @n || ']'
```

`||` is the unambiguous string concatenation operator (Oracle/PostgreSQL standard).
`+` remains supported but is ambiguous (also performs numeric addition).
**Prefer `||` for strings, `+` for numbers.**

### 5.9 BOOL Type

```spl
-- Declaration
WORKFLOW check_doc
    INPUT:  @text TEXT, @strict BOOL DEFAULT FALSE
    OUTPUT: @passed BOOL
DO
    CALL has_pii(@text) INTO @passed         -- deterministic tool returns 'true'/'false'

    EVALUATE @passed
        WHEN = TRUE THEN
            LOGGING f'PII detected — strict={@strict}' LEVEL WARN
            COMMIT 'rejected' WITH passed = 'false'
        ELSE
            COMMIT 'approved' WITH passed = 'true'
    END
END
```

`TRUE` and `FALSE` are first-class literals. Boolean variables evaluate naturally in `EVALUATE` conditions — no numeric conversion needed. Prefer `BOOL` over `NUMBER` for flags and predicates: it signals intent explicitly and makes workflows self-documenting.

### 5.11 Native LIST Type

```spl
@summaries := []                                  -- empty list
@summaries := list_append(@summaries, @item)      -- append
@text := list_concat(@summaries, '\n')            -- join to string
@n := list_count(@summaries)                      -- length
@item := list_get(@summaries, 0)                  -- index access
```

Lists are represented as JSON arrays internally. All list operations are deterministic built-ins — zero tokens.

### 5.12 Pipe Operator — `|` *(planned)*

```spl
GENERATE extract(@doc) | summarize() | translate('Spanish') INTO @result
```

Chains GENERATE steps: each step's output becomes the next step's input. No intermediate variables needed. Inspired by Unix pipes and functional composition.

---

## 6. The Bigger Picture

SPL is not trying to replace Python, SQL, or Bash. It is a *composition layer* — the language in which you express the *orchestration* of AI workflows, calling out to deterministic Python tools where precision is needed and to LLMs where judgment is needed.

The analogy: just as a musical score is not the same as the instruments, SPL is not the compute itself — it is the notation that lets any developer write their own symphony and have it played by the AI orchestra.

PL/SQL's success came not from SQL, but from giving data engineers one language to express both what they wanted (SQL) and how to get it (procedural logic). Oracle became irreplaceable because once you wrote in PL/SQL, everything *composed*.

SPL's bet is the same: give AI developers one language where declarative LLM invocation, deterministic polyglot tools, bash-style composition, and globally distributed execution all live together — and the language becomes the natural medium for an entire generation of GenAI applications.

---

## 7. The Road Ahead

### SPL v2.0 — Where We Are Today

Text in, text out. Workflows that call LLMs, invoke deterministic tools, handle exceptions, and run on Momagrid. The foundation is solid: the grammar is orthogonal, the runtime is efficient, the language is readable by anyone.

### SPL v3.0 — Multimodal

This is why **Simple** is the right name and not a limitation.

When SPL v3.0 arrives, `INPUT` and `OUTPUT` will extend beyond `TEXT` to carry `IMAGE`, `AUDIO`, and `VIDEO` as first-class types. The language does not change. The keywords do not multiply. The programmer writes the same clean workflows — the type system simply grows richer.

```spl
-- v3.0: image understanding
WORKFLOW analyze_product_photo
    INPUT:  @photo IMAGE, @question TEXT
    OUTPUT: @answer TEXT
DO
    GENERATE describe_image(@photo) INTO @description
    GENERATE answer(@question, @description) INTO @answer
    COMMIT @answer
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

-- v3.0: video analysis
WORKFLOW content_moderation
    INPUT:  @clip VIDEO
    OUTPUT: @verdict TEXT, @confidence NUMBER
DO
    CALL extract_frames(@clip, fps=1) INTO @frames      -- deterministic
    GENERATE classify_frames(@frames) INTO @verdict
    GENERATE confidence_score(@verdict) INTO @confidence
    EVALUATE @confidence
        WHEN > 0.9 THEN COMMIT @verdict WITH status = 'certain'
        ELSE             COMMIT @verdict WITH status = 'review'
    END
END
```

The simplicity scales. A developer who knows SPL v2.0 reads v3.0 instantly — the new types are self-evident, the new CALL tools handle format conversion deterministically, and GENERATE handles judgment as always. No new control flow. No new keywords. Just richer data.

### The Type Progression

| Version | Types | Era |
|---------|-------|-----|
| SPL v1.0 | `TEXT` | Prompt engineering |
| SPL v2.0 | `TEXT`, `NUMBER`, `BOOL`, `LIST` | Agentic workflows |
| SPL v3.0 | `TEXT`, `NUMBER`, `BOOL`, `LIST`, `IMAGE`, `AUDIO`, `VIDEO` | Multimodal AI |
| SPL v4.0 | + `STREAM`, `GRAPH`, `SENSOR` | Physical world integration — IoT, camera feeds, real-time data |

In each version, the *language* stays simple. The *world it can describe* grows larger.

### Why "Simple" Is the Right Name Forever

A language named "Structured Prompt Language" would have aged out the moment multimodal arrived — prompts are text, and text is just one modality. A language named "Simple Programming Language" makes no such promise about modality. It promises only one thing: **that expressing what you want should never be harder than the thing itself.**

That promise holds for text. It holds for images. It holds for audio and video. It will hold for whatever modalities come next. Simplicity is not a feature — it is the design commitment that all features are measured against.

---

## 8. Revision History

| Date | Change |
|------|--------|
| 2026-03-24 | Initial design document — Wen + Claude |
| 2026-03-24 | Added dualistic runtime section, OTHERWISE→ELSE, f-strings, LIST, `\|\|`, LOGGING levels |
| 2026-03-24 | Renamed "Dualistic" → "Efficient Runtime"; added polyglot tools dimension; added Momagrid as Dimension 4 |
| 2026-03-24 | SPL elevated: "Structured Prompt Language" → "Simple Programming Language" — same acronym, universal identity |
| 2026-03-24 | Added "The Road Ahead" — SPL v3.0 multimodal vision (IMAGE, AUDIO, VIDEO types) |
| 2026-03-24 | Added BOOL type — TRUE/FALSE literals, type annotation, EVALUATE boolean conditions |
| 2026-03-24 | Added Section 0 (naming evolution); practical synthesis framing in Section 2 |
| 2026-03-24 | Log extension: `.log` → `.md`; recipe 13 tools.py — chunk_plan/extract_chunk as deterministic CALL |
