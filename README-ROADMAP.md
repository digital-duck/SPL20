# SPL 2.0 — Roadmap

This document captures planned features, design principles, and architectural decisions for future SPL 2.0 development.

---

## Design Principles

### 1. Minimal new syntax
Before adding a keyword, exhaust existing constructs. New syntax has a learning cost and a maintenance cost. If `CALL`, `SELECT`, or `GENERATE` can express the idea, use them.

### 2. Fail-fast over "smart" fallback
SPL does not silently fall back to another backend when one fails. If a connector, adapter, or model is unavailable, it raises an error immediately. This surfaces misconfiguration early and keeps behavior predictable.

Resilience is expressed through **defaults**, not fallbacks:
- `INPUT: @max_iterations int DEFAULT 5` — caller can override, but there is always a known value
- `--adapter ollama` — explicit at the call site, no auto-discovery
- `--connector transcribe=whisper` — explicit backend, no guessing

### 3. No hardcoding
Tuneable values belong in `INPUT` parameters with defaults. Hardcoding a value makes the decision for the end-user before they can ask. See cookbook recipes for examples of this pattern applied consistently.

### 4. Backend-agnostic by design
SPL code is portable across backends. The same `.spl` file runs against Ollama, OpenAI, Anthropic, or Momagrid by changing a CLI flag — not the source. The same principle extends to Tool Connectors.

---

## Planned Feature: Tool Connectors

### Motivation

SPL 2.0 already abstracts LLM backends via `--adapter`. The same abstraction is needed for non-LLM operations: format conversion, transcription, OCR, text-to-speech, etc. Without this, workflows leak into bash scripts or Python glue code — defeating the declarative model.

### Design

Tool connectors mirror the adapter pattern:

```bash
# Adapter: swappable LLM backend
spl2 run script.spl --adapter ollama -m gemma3

# Connector: swappable tool backend  (proposed)
spl2 run script.spl --connector pdf=pymupdf --connector transcribe=whisper
```

Defaults are declared in `.spl/connectors.yaml`:

```yaml
connectors:
  pdf:
    backend: pymupdf
    options:
      preserve_tables: true
  transcribe:
    backend: whisper
    model: base
    lang: en
  tts:
    backend: piper
    voice: en-us
  ocr:
    backend: tesseract
    lang: eng
```

### SPL Syntax

Tool connectors surface through two existing constructs — no new keywords required:

**In `SELECT` (input preprocessing):**
```sql
-- PDF ingestion before LLM analysis
PROMPT analyze_research
SELECT
    tool.pdf_to_md(context.pdf_path) AS content,
    context.question AS question
GENERATE answer(question, content)
```

**Via `CALL` in `WORKFLOW` (as a named step):**
```sql
WORKFLOW transcribe_and_summarize
    INPUT: @audio_path TEXT, @lang TEXT DEFAULT 'en'
    OUTPUT: @summary TEXT
DO
    CALL tool.transcribe(@audio_path, lang=@lang) INTO @transcript
    GENERATE summarize(@transcript) INTO @summary
    COMMIT @summary WITH status = 'complete'
END
```

### Built-in tool functions

| Function | Direction | Default backend |
|---|---|---|
| `tool.pdf_to_md(file)` | PDF → Markdown | pymupdf |
| `tool.md_to_pdf(text)` | Markdown → PDF | pandoc |
| `tool.transcribe(file, lang)` | Audio → Text | whisper |
| `tool.tts(text, voice)` | Text → Audio | piper |
| `tool.ocr(image)` | Image → Text | tesseract |
| `tool.caption(image)` | Image → Text | llava (multimodal LLM) |
| `tool.convert(file, from=, to=)` | Generic | auto-select |

`tool.convert()` is the generic escape hatch. All named functions are convenience wrappers over it.

### Fail-fast behaviour

If a connector backend is not installed or misconfigured, SPL raises immediately:

```
Error: connector 'transcribe' backend 'whisper' not found.
Install with: pip install openai-whisper
Or override with: --connector transcribe=assemblyai
```

No silent fallback. No auto-discovery. The user is told exactly what to fix.

### Multimodal LLMs as connectors

Vision-capable models (LLaVA, GPT-4o) are connectors, not special syntax. `tool.caption(image)` routes to the configured multimodal backend — swappable like any other.

---

## Text2SPL Compiler

### What it does

`Text2SPL` converts a plain-English task description into valid SPL 2.0 source code. It is implemented in `spl2/text2spl.py` and is adapter-agnostic — it works with any `LLMAdapter` (Ollama, OpenAI, Anthropic, etc.).

### Architecture

```
Natural language description
         │
         ▼
  LLM (via adapter)  ←── SPL2_SYSTEM_PROMPT
         │                 (syntax reference + 4 worked examples)
         ▼
    raw SPL text
         │
         ▼
  validate_output()  ←── Lexer → Parser → Analyzer  (3-stage)
         │
         ├── valid  ──► return SPL source
         └── error  ──► feed error + code back to LLM (up to 2 retries)
```

**Compile-validate-retry loop** — the real SPL parser/lexer/analyzer is used as the oracle. If the LLM produces syntactically invalid SPL, the exact error message is fed back at lower temperature (0.2) for self-correction, up to `max_retries` times.

### Modes

| Mode | Behaviour |
|------|-----------|
| `auto` | LLM decides whether PROMPT or WORKFLOW best fits the task |
| `prompt` | Force a single PROMPT statement |
| `workflow` | Force a WORKFLOW with full control flow |

### CLI usage

```bash
# compile natural language to SPL (proposed spl2 compile command)
spl2 compile "summarize a PDF and store the result" --mode workflow
spl2 compile "translate an email to French" --adapter ollama -m gemma3
```

### Model selection

No model is hardcoded — the caller controls adapter and model via CLI flags, the same as `spl2 run`. However, **a dedicated code-generation model is strongly recommended** for Text2SPL:

- Code-specialised models (e.g. `deepseek-coder`, `codestral`, `qwen2.5-coder`, `claude-sonnet`) produce structurally cleaner output and hallucinate less syntax.
- Using a general-purpose chat model for code generation wastes capability and increases retry rate.
- Recommended pattern: add a `text2spl` entry to the adapter config so users can override it once rather than on every invocation.

This is tracked in the Backlog as **dedicated Text2SPL model config**.

---

## Planned Feature: Code-RAG for Text2SPL

> **Status: Deferred — Research Track**
>
> Full implementation (live pair capture, DB pruning, fine-tuning pipeline) is deferred until the SPL language spec stabilises enough to justify training a specialty model.
>
> **Development workaround (active):** Use the `claude_cli` adapter with `claude-sonnet-4-6` as the Text2SPL compiler. This avoids VRAM pressure entirely (runs via Claude subscription, no local model loaded) and produces the highest-quality `(NL, SPL)` training pairs available — Sonnet 4.6 becomes the **reference oracle** whose outputs will seed fine-tuning of the future specialty model.
>
> ```bash
> spl2 compile "build a review agent that refines until quality > 0.8" \
>   --adapter claude_cli -m claude-sonnet-4-6 --mode workflow
> ```
>
> The design below is fully specified and ready to implement when the time is right.

### Motivation

The current `Text2SPL` compiler embeds 4 hand-written examples in the system prompt. This has two limitations:

1. **Coverage** — 4 examples cannot cover all SPL patterns (CTEs, multi-CTE fan-out, EVALUATE, WHILE, PROCEDURE, exception handling, tool connectors, etc.).
2. **Staleness** — as the SPL spec evolves and new cookbook recipes are added, the examples in the prompt must be manually updated.

**Code-RAG** replaces the static examples with a living knowledge base that grows continuously and feeds a self-improving training loop for a dedicated SPL model.

### Self-Learning Flywheel

The core insight is that every successful `spl2 compile` invocation produces a validated `(description, SPL)` pair — a free training signal. Combined with the existing cookbook corpus and user-contributed recipes, the system gets smarter every time it is used.

```
          ┌─────────────────────────────────────────────────┐
          │              Self-Learning Flywheel              │
          │                                                  │
          │   Cookbook recipes                               │
          │        +                                         │
          │   User invocations  ──► validated (NL, SPL) pair │
          │        +                       │                 │
          │   Dynamically generated SPL    │                 │
          │                                ▼                 │
          │                       Code-RAG Vector DB         │
          │                                │                 │
          │              ┌─────────────────┴───────────┐     │
          │              ▼                             ▼     │
          │    Retrieval at compile time      Pruning &      │
          │    (top-k examples injected       deduplication  │
          │     into prompt)                      │          │
          │                                       ▼          │
          │                              Fine-tune dataset   │
          │                                       │          │
          │                                       ▼          │
          │                           Specialty SPL model    │
          │                           (e.g. Qwen-Coder       │
          │                            fine-tuned on SPL)    │
          │                                       │          │
          │                                       └──► replaces general-purpose LLM
          └─────────────────────────────────────────────────┘
```

**Three feedback loops operating at different timescales:**

| Loop | Trigger | Effect |
|------|---------|--------|
| **Compile-time RAG** | Every `spl2 compile` call | Top-k similar examples injected into prompt immediately |
| **DB growth** | Every validated (NL, SPL) pair | Vector DB expands; future retrievals improve |
| **Model fine-tuning** | Scheduled / when DB reaches threshold | Specialty SPL model retrained on curated pairs; general LLM no longer needed |

### Knowledge Base Sources

All `(description, SPL)` pairs are eligible, regardless of origin:

| Source | Quality signal |
|--------|---------------|
| Cookbook recipes (`cookbook/*/`) | Hand-curated; highest quality |
| User `spl2 compile` invocations | Validated by parser+analyzer; auto-accepted |
| Dynamically generated SPL (from workflows calling `Text2SPL`) | Validated; accepted if no retry needed |
| Rejected/retried generations | Stored as negative examples for fine-tuning |

### Vector DB Design

```
Indexing pipeline  (triggered on new pair, or batch-rebuild)
┌──────────────────────────────────────────────────────────────┐
│  for each (description, spl_source) pair:                    │
│    embed description → vector                                │
│    store { vector, spl_source, metadata } in index           │
│    metadata: { source, category, timestamp, retry_count,     │
│                quality_score, model_used }                   │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
  Vector index (spl2 built-in VectorStore, or Chroma / FAISS)

At compile time:
  NL description
       │ embed
       ▼
  similarity search  →  top-k SPL examples  (k=3..5)
       │
       ▼
  inject examples into system prompt  (replacing static examples)
       │
       ▼
  LLM generates SPL  (validate-retry loop as before)
```

### Indexing sources

| Source | What is indexed |
|--------|----------------|
| `cookbook/*/` `.spl` files | Full SPL source as the "answer" |
| `cookbook_catalog.json` | `description` and `category` as the search target |
| Inline `-- comment` headers in `.spl` files | Optional richer description |

### SPL source for the indexer (self-hosted example)

The indexer can itself be written as a WORKFLOW in SPL — eating our own cooking:

```sql
WORKFLOW build_code_rag_index
  INPUT @recipe_dir TEXT DEFAULT './cookbook'
  OUTPUT @index_path TEXT DEFAULT '.spl/code_rag.index'
DO
  -- read catalog, embed descriptions, store SPL source
  CALL tool.glob(@recipe_dir, pattern='**/*.spl') INTO @spl_files
  WHILE @spl_files NOT empty DO
    CALL tool.read_file(@spl_files[0]) INTO @spl_source
    GENERATE extract_metadata(@spl_source) INTO @meta
    CALL memory.embed(@meta.description, payload=@spl_source) INTO @_
    @spl_files := @spl_files[1:]
  END
  @index_path := memory.flush()
  COMMIT @index_path
END;
```

### Retrieval at compile time

```python
# Pseudocode — to be added to Text2SPL.compile()
async def _retrieve_examples(self, description: str, k: int = 4) -> str:
    hits = await self.rag_store.query(description, top_k=k)
    return "\n\n".join(
        f"-- Example: {h.metadata['name']}\n{h.payload}"
        for h in hits
    )
```

The retrieved block replaces the static `== EXAMPLES ==` section in `SPL2_SYSTEM_PROMPT`.

### Benefits

- **Better coverage** — every new cookbook recipe automatically improves Text2SPL quality.
- **No manual prompt maintenance** — examples stay in sync with the language spec by construction.
- **Semantic retrieval** — if the user asks for "a loop that refines text until quality is high enough", the WHILE-loop quality-gate recipe is retrieved rather than a generic summarisation example.
- **Category steering** — recipes tagged `agentic`, `rag`, `multi-model`, etc. can be preferentially retrieved for matching task types.

### Pruning and Optimisation

As the vector DB grows it needs curation — not all (NL, SPL) pairs are equally useful:

- **Deduplication** — semantically near-duplicate descriptions are merged; the highest-quality SPL is kept.
- **Quality scoring** — pairs where `retry_count=0` score higher than those that needed correction.
- **Coverage pruning** — pairs that are already well-covered by the fine-tuned model are retired from the active RAG DB, keeping retrieval fast and relevant.
- **Negative mining** — rejected generations (those that never validated) are kept as negative examples to steer fine-tuning away from known failure modes.

### Specialty SPL Model

The long-term goal is a model that no longer needs RAG at all — one that has internalised the SPL grammar, idioms, and patterns through fine-tuning:

```
General LLM + Code-RAG  →  (fine-tuning)  →  Specialty SPL model
                                              (Qwen-Coder-SPL, etc.)
```

- **Base**: Qwen2.5-Coder or similar code-specialised open model
- **Training data**: curated (description, SPL) pairs exported from the vector DB
- **Validation**: every training example has already been validated by the SPL parser+analyzer — the dataset is clean by construction
- **Deployment**: runs locally via Ollama; no API dependency; fast and private
- **Iteration**: model is periodically retrained as the recipe corpus and user-generated pairs grow

### Implementation Phases

| Phase | Scope |
|-------|-------|
| 1 — Offline indexer | `spl2 index-recipes` command; embeds all cookbook `.spl` files into the built-in `VectorStore` |
| 2 — Dynamic retrieval | `Text2SPL` accepts optional `rag_store`; injects top-k examples at compile time |
| 3 — Live pair capture | Every validated `spl2 compile` invocation appends `(description, SPL)` to the DB automatically |
| 4 — Self-indexing | Indexer workflow written in SPL; triggered when a recipe is added or updated |
| 5 — DB pruning | Deduplication, quality scoring, and coverage-based retirement of stale pairs |
| 6 — Fine-tune export | `spl2 export-training-data` — exports curated pairs as JSONL for model fine-tuning |
| 7 — Specialty model | Fine-tune Qwen2.5-Coder (or equivalent) on exported dataset; deploy via Ollama as `spl-coder` |
| 8 — Model-replaces-RAG | Specialty model is good enough that RAG retrieval becomes optional (fallback only) |

---

## Near-term Parser Fixes

Three cookbook recipes currently fail due to parser gaps:

| Recipe | Error | Fix needed |
|--------|-------|------------|
| 13 Map-Reduce | `EVALUATE @score WHEN > 0.7` | Numeric comparison in EVALUATE |
| 14 Multi-Agent | `@result :=` inside PROCEDURE | Variable assignment in PROCEDURE body |
| 19 Memory Chat | `SELECT memory.get('key') INTO @var` | Function call in SELECT inside WORKFLOW |

---

## Backlog

- `PARALLEL DO ... END` — run independent GENERATE calls concurrently
- `STREAM INTO @var` — streaming token output for long generations
- `spl2 memory` CLI — read/write/delete named memory slots from the command line
- Workflow-level memory writes (`STORE @var IN memory.key`) — currently stubbed out
- `spl2 test` — built-in test runner for `.spl` files with expected output matching
- `spl2 compile` — CLI command for Text2SPL (natural language → SPL source)
- Dedicated Text2SPL model config — allow users to pin a code-generation model (e.g. `deepseek-coder`, `qwen2.5-coder`) for `spl2 compile` separately from the runtime model used by `spl2 run`
- `spl2 index-recipes` — offline indexer that embeds all cookbook `.spl` files into the vector store for Code-RAG retrieval
