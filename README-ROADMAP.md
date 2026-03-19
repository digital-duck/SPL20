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
