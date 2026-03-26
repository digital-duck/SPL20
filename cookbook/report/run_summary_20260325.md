# SPL 2.0 Cookbook — Run Summary 2026-03-25

## Result: 37/37 Success (total 1000.0s)

---

## Comparison: 2026-03-25 vs 2026-03-24

| Metric | 2026-03-24 | 2026-03-25 | Delta |
|--------|-----------|-----------|-------|
| **Pass rate** | 37/37 | **37/37** | No change |
| **Total time** | 1763.2s | **1000.0s** | **-763.2s (-43.3%)** |

**Key win:** Significant runtime reduction of 763.2s (-43.3%) with no functional regression. All 37 recipes continue to pass.

The previous day's time spike was largely attributed to recipe #12 (Plan and Execute: 508.5s). Today's run suggests LLM response latency returned to normal levels.

---

## Changes Applied Today

### Recipes enhanced with intermediate file writes

| Recipe | File | Change |
|--------|------|--------|
| #14 Multi-Agent Collaboration | `multi_agent.spl` | Write `research.md`, `analysis.md`, `report.md` to `@log_dir` after each agent |
| #15 Automated Code Review | `code_review.spl` | Added `@log_dir` INPUT param; write `security.md`, `performance.md`, `style.md`, `bugs.md`, `review.md`; file writes in exception handlers |

### RETRY infinite-loop guard — LIMIT 3 applied across all recipes

| Recipe | File |
|--------|------|
| #07 Safe Generation | `safe_generation.spl` |
| #17 Tree of Thought | `tree_of_thought.spl` |
| #18 Guardrails Pipeline | `guardrails.spl` |
| #20 Ensemble Voting | `ensemble.spl` |

Recipe #14 already had `LIMIT 3` from yesterday's session.

### Recipe #17 Tree of Thought — 3-model diversification

Added `@model_a`, `@model_b`, `@model_c` as configurable INPUT params (defaults: `gemma3`, `phi4`, `qwen2.5`). Each reasoning path now uses a distinct model via `USING MODEL @model_x` for both the initial approach and development steps. Scoring and synthesis remain on the default adapter as a neutral judge.

---

## Status

All 37/37 recipes passing. Runtime back to healthy levels (1000s vs 1763s yesterday).
