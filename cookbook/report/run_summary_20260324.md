# SPL 2.0 Cookbook — Run Summary 2026-03-24

## Result: 37/37 Success (total 1763.2s)

---

## Comparison: 2026-03-24 vs 2026-03-23

| Metric | 2026-03-23 | 2026-03-24 | Delta |
|--------|-----------|-----------|-------|
| **Pass rate** | 36/37 | **37/37** | +1 fixed |
| **Total time** | 1378.8s | 1763.2s | +384.4s |

### What changed

| ID | Recipe | 03-23 | 03-24 | Delta |
|----|--------|-------|-------|-------|
| **18** | Guardrails Pipeline | **FAILED (0.2s)** | **OK (30.9s)** | Fixed |
| 12 | Plan and Execute | 266.8s | 508.5s | +241.7s |
| 16 | Reflection Agent | 136.9s | 158.1s | +21.2s |
| 33 | Interview Simulator | 150.6s | 173.6s | +23.0s |
| 26 | Prompt A/B Test | 37.2s | 48.0s | +10.8s |
| 14 | Multi-Agent Collaboration | 88.6s | 74.8s | -13.8s |

**Key win:** Recipe #18 (Guardrails Pipeline) went from FAILED to OK — the only failure yesterday is now resolved.

**Time regression:** The extra ~384s is largely driven by recipe #12 (Plan and Execute: 508s vs 267s yesterday). This recipe involves multi-step planning and is sensitive to LLM response latency/output length. No functional regression — all 37 recipes pass.

---

## Fixes Applied Today

### Recipe #22 (Text2SPL Demo) — Misplaced `generated/` folder

**Problem:** `text2spl_demo.sh` used `OUTDIR="cookbook/22_text2spl_demo/generated"` as a relative path, but `run_all.py` already sets `cwd=cookbook/`. This produced a nested `cookbook/cookbook/22_text2spl_demo/generated/` directory that was being tracked by git.

**Fix:** Changed `OUTDIR` in `text2spl_demo.sh` to `"22_text2spl_demo/generated"` (relative to the `cookbook/` cwd). Removed the misplaced `cookbook/cookbook/` tree from git and filesystem.

**Files changed:**
- `cookbook/22_text2spl_demo/text2spl_demo.sh` — OUTDIR path corrected
- `cookbook/cookbook/` — deleted (git rm -rf)

---

## SPL Grammar Enhancement — LOGGING Statement

### Motivation

Recipe #13 (Map-Reduce Summarizer) and similar WHILE-loop-heavy workflows have no way to emit intermediate state during execution. Python's `print()` equivalent was missing from the language.

### Design

```
LOGGING <expr>               -- write to stdout (default)
LOGGING <expr> TO 'file'     -- append to OS file with timestamp
```

### Changes

| File | Change |
|------|--------|
| `spl/tokens.py` | Added `LOGGING` and `TO` token types + keyword entries |
| `spl/ast_nodes.py` | Added `LoggingStatement(expression, destination)` node; added to `Statement` union |
| `spl/parser.py` | Added `_parse_logging_statement()` + dispatch in `_parse_statement()` |
| `spl/executor.py` | Added `_exec_logging()` — console print or file append with ISO timestamp |

### Usage examples

```spl
-- Console output (default)
LOGGING 'Starting map-reduce | document length: ' + @document
LOGGING '[Chunk ' + @chunk_index + '/' + @chunk_count + '] ' + @chunk_summary

-- Write to file (appended, with timestamp)
LOGGING @debug_info TO 'workflow_debug.log'
```

---

## Recipe #13 Improvement — LIST type for `@summaries`

### Before

```spl
@summaries := ''
@summaries := @summaries + '\n[Chunk ' + @chunk_index + ']: ' + @chunk_summary
GENERATE reduce_summaries(@summaries, @style) INTO @final_summary
```

The string concatenation was manual and fragile; @summaries was passed directly to reduce_summaries without a clear separation between list-building and list-consuming steps.

### After

```spl
@summaries := []          -- LIST: accumulates per-chunk summaries
@summaries := list_append(@summaries, @chunk_summary)
...
@summaries_text := list_concat(@summaries, '\n')
GENERATE reduce_summaries(@summaries_text, @style) INTO @final_summary
```

**Key improvements:**
- `@summaries` is typed as LIST — intent is explicit
- `list_append()` / `list_concat()` as semantic operations (clean separation of accumulation vs. reduction)
- `@summaries_text` is a named intermediate — the concat-before-reduce step is now visible
- Exception handlers also updated: both `ContextLengthExceeded` and `BudgetExceeded` now do explicit `list_concat` before calling reduce
- LOGGING added inside the WHILE loop to show per-chunk progress

---

## Status

All 37/37 recipes passing. Ready to continue recipe review from #13 onward.
