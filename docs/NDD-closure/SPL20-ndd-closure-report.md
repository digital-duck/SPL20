# NDD Closure Report: SPL 2.0

**Method:** `J(S, E(G(S)))`

- `S` = `SPL-design-v1.1.md` → updated to `v1.2` after this audit
- `G(S)` = `/home/gong-mini/projects/digital-duck/SPL20/spl/` — implementation
- `E(G(S))` = `SPL20-user-guide.md` — spec extracted from code by human review
- `J` = structured diff below

**Audit verdict: [DIVERGED]** — four gaps found
**Post-fix verdict: [CLOSED]** — all four gaps resolved in v1.2 (2026-04-12)

The core language is faithfully implemented. The divergences were in exception
semantics, keyword naming, missing features, and significant undocumented additions.
All four were closed by updating the spec to v1.2 and patching the executor/parser.

---

## Constraint Checklist (from SPL-design-v1.1.md)

### Section 2 — Three-Language Synthesis

| # | Constraint from Design Doc | Coverage in Code | Status |
|---|---------------------------|------------------|--------|
| 1 | `GENERATE` for probabilistic LLM calls | Implemented | CLOSED |
| 2 | `CALL` for deterministic, zero-token operations | Implemented | CLOSED |
| 3 | `WHILE` loops (index-based) | Implemented | CLOSED |
| 4 | `EVALUATE/WHEN/ELSE` branching | Implemented | CLOSED |
| 5 | `EXCEPTION` handling | Implemented | CLOSED |
| 6 | `||` string concatenation | Implemented (`BinaryOp`, `op == '\|\|'`) | CLOSED |
| 7 | Pipe operator `\|` chaining GENERATEs | Implemented (chained `GenerateClause`) | CLOSED |
| 8 | `@var` variable substitution | Implemented | CLOSED |
| 9 | `$$...$$` here-doc string bodies | Implemented | CLOSED |
| 10 | `LOGGING ... TO 'file'` redirection | Implemented | CLOSED |

### Section 4 — Efficient Runtime

| # | Constraint | Coverage | Status |
|---|-----------|----------|--------|
| 11 | GENERATE costs tokens; CALL costs zero | Enforced by executor | CLOSED |
| 12 | `USING MODEL @var` per-GENERATE model override | Implemented | CLOSED |
| 13 | `WITH OUTPUT BUDGET n TOKENS` | Implemented (`output_budget`) | CLOSED |
| 14 | `WITH TEMPERATURE x` | Implemented | CLOSED |
| 15 | Polyglot tools via `--tools` Python callable | Implemented (`@spl_tool`, `register_tool`) | CLOSED |
| 16 | Built-ins: `list_append`, `list_concat`, `list_count`, `list_get` | Implemented | CLOSED |
| 17 | Built-ins: `write_file`, `read_file` | Implemented | CLOSED |
| 18 | Built-ins: `len`, `upper`, `lower`, `truncate` | Implemented | CLOSED |
| 19 | Batch/async execution model (no streaming) | Implemented | CLOSED |
| 20 | Momagrid adapter for distributed execution | Adapter present (`momagrid.py`) | CLOSED |

### Section 5 — Language Features

| # | Constraint | Coverage | Status |
|---|-----------|----------|--------|
| 21 | `WORKFLOW` with `INPUT`/`OUTPUT`/`DO`/`EXCEPTION`/`END` | Implemented | CLOSED |
| 22 | `DEFAULT` values for INPUT params | Implemented | CLOSED |
| 23 | `GENERATE func(args) INTO @var` | Implemented | CLOSED |
| 24 | `CALL tool(args) INTO @var` | Implemented | CLOSED |
| 25 | `EVALUATE` numeric comparison (`>`, `<`, `>=`, `<=`, `=`, `!=`) | Implemented | CLOSED |
| 26 | `EVALUATE` string equality (`WHEN = 'value'`) | Implemented | CLOSED |
| 27 | `EVALUATE` string predicate `WHEN STARTSWITH` | Implemented | CLOSED |
| 28 | `EVALUATE` boolean `WHEN TRUE` / `WHEN FALSE` | Implemented | CLOSED |
| 29 | `EVALUATE` semantic `WHEN ~ 'condition'` (LLM-judged) | Implemented | CLOSED |
| 30 | `WHILE @i < @n DO ... END` (index-based) | Implemented | CLOSED |
| **31** | **`WHILE @item IN @items DO ... END` (collection-based)** | **`__in_list__` in parser but no item-variable assignment in executor — body executes but `@item` is never bound** | **MISSING** |
| 32 | `EXCEPTION WHEN ExceptionType THEN` | Implemented | CLOSED |
| 33 | `RETRY WITH temperature=x LIMIT n` | Implemented | CLOSED |
| 34 | `RETRY` default limit 3 if `LIMIT` omitted | Implemented | CLOSED |
| 35 | `LOGGING expr LEVEL DEBUG\|INFO\|WARN\|ERROR` | Implemented | CLOSED |
| 36 | `LOGGING expr TO 'file'` | Implemented | CLOSED |
| 37 | f-string `f'text {@var} text'` | Implemented | CLOSED |
| 38 | `||` preferred over `+` for strings | Both work; preference is convention, not enforced | CLOSED |
| 39 | `BOOL` type, `TRUE`/`FALSE` literals | Implemented | CLOSED |
| 40 | `LIST` type, `[]` literal | Implemented | CLOSED |
| 41 | `COMMIT @result WITH status='...'` | **`COMMIT` is a deprecated alias; primary keyword is `RETURN`** | DIVERGED |
| 42 | `HallucinationDetected` — runtime confidence threshold | **Only raised via explicit `RAISE HallucinationDetected`; no automatic threshold checking exists** | DIVERGED |
| **43** | **`ToolFailed` exception type** | **Not registered in `EXCEPTION_CLASSES`; tool errors propagate as raw Python exceptions, not catchable by `WHEN ToolFailed`** | **MISSING** |

---

## Summary of Divergences

### [MISSING] Constraints — these are in the spec but absent or broken in code

**1. `WHILE @item IN @items` — collection iteration variable**

The design doc states: *"Collection-based iteration (LIST-aware): `WHILE @item IN @items DO`"*.
The parser produces an `__in_list__` FunctionCall for `IN` syntax, but the
executor's `_exec_while` has no code path that assigns `@item` to each element
of `@items`. The loop body executes, but the iteration variable is never bound.
Effectively, collection-based WHILE is not implemented.

**2. `ToolFailed` exception**

The design doc lists `ToolFailed` as a first-class exception type raised when
"deterministic CALL threw". It is not in `EXCEPTION_CLASSES`. A Python exception
raised by a CALL tool bubbles up as a raw exception, bypassing the SPL exception
system entirely — `WHEN ToolFailed THEN` is silently unreachable.

**3. `HallucinationDetected` — automatic confidence threshold**

The design doc states: *"Post-generation confidence check failed. The runtime
can be configured with a confidence threshold."* In the code, there is no such
threshold. `HallucinationDetected` is only raised by `RAISE HallucinationDetected`
in the workflow body. Developers expecting the runtime to auto-detect hallucinations
will be surprised.

---

### [ADDED] — in code, not in design doc

These are significant additions that users will encounter but that the design
doc does not mention.

**1. MAP type and eight map_* built-ins**

`map()`, `map_get`, `map_set`, `map_keys`, `map_values`, `map_merge`,
`map_has`, `map_delete` — a complete key-value type, absent from the design doc.

**2. RETURN vs COMMIT**

The executor treats `COMMIT` as a deprecated alias; `RETURN` is the primary
keyword. The design doc only mentions `COMMIT`. Production code should prefer
`RETURN`.

**3. WHEN OTHERS catch-all**

`WHEN OTHERS THEN` matches any unhandled exception. Not in the design doc but
implemented and recommended in error messages from the runtime itself.

**4. DO block (inline exception handling)**

```spl
DO
    GENERATE risky(@input) INTO @result
EXCEPTION
    WHEN RefusalToAnswer THEN
        @result := 'fallback'
END
```

Inline exception scope within a workflow body — not described in the design doc.

**5. STORAGE type and subscript assignment**

```spl
@store STORAGE DEFAULT 'sqlite:data.db'
@store['key'] := @value
```

A backend-connected storage type for durable key-value access within workflows.
Not in the design doc.

**6. SELECT INTO (multi-variable CTE fan-out)**

```spl
WITH cte_a AS (PROMPT ...), cte_b AS (PROMPT ...)
SELECT cte_a.result, cte_b.result
INTO @result_a, @result_b
```

Parallel PROMPT execution with fan-out assignment. Not in the design doc.

**7. LLM fallback for unresolved CALL targets**

When `CALL unknown_proc(...)` finds no tool, built-in, or SPL procedure,
the executor silently calls the LLM to "simulate" the procedure with a generic
prompt. This is undocumented behavior that can waste tokens and produce
unexpected results. The design doc says CALL always costs zero tokens.

**8. Additional exceptions not in spec**

`QualityBelowThreshold`, `MaxIterationsReached`, `NodeUnavailable`,
`ModelUnavailable` (SPL3-class), `FileNotFound`, `UnsupportedFormat`,
`CodecError`, `NoAudioTrack`, `InvalidTimestamp` — the last five are v3.0
multimodal exceptions already present in the v2.0 runtime.

**9. CLI commands beyond `run`**

`spl validate`, `spl explain`, `spl text2spl`, `spl memory`, `spl doc-rag`,
`spl code-rag`, `spl config`, `spl adapters` — none described in the design doc.

**10. Prompt cache**

Optional prompt deduplication via SHA-256 hash of `model + prompt`.
Zero-cost repeat calls for identical inputs. Not in the design doc.

**11. Prompt logging (`--log-prompts`)**

Writes each assembled prompt to a numbered `.md` file. Mentioned as future
tooling in the design doc; it is implemented now.

---

## Closure Assessment

| Area | Verdict |
|------|---------|
| Core language (GENERATE, CALL, EVALUATE, WHILE index, EXCEPTION, RETRY, LOGGING, types) | CLOSED |
| Pipe operator `\|` | CLOSED |
| WHILE collection-based iteration | DIVERGED — spec says implemented, code is broken |
| `ToolFailed` exception | DIVERGED — in spec, not in runtime |
| `HallucinationDetected` auto-detection | DIVERGED — spec implies runtime detection, code requires explicit RAISE |
| `COMMIT` keyword | DIVERGED — deprecated in code, primary in spec |
| MAP type | ADDED — not in spec, fully implemented |
| `WHEN OTHERS` | ADDED — not in spec, implemented |
| LLM fallback for unresolved CALL | ADDED — contradicts "CALL = zero tokens" principle |
| SPL3 exceptions in v2.0 code | ADDED — forward-ported |

**Overall: [DIVERGED]**

The language core is solid and the spec is largely honoured. The four
divergences above are the areas where the spec and the runtime make different
promises to users.

---

*Generated: 2026-04-12 by human code review of SPL20/spl/ against SPL-design-v1.1.md*
