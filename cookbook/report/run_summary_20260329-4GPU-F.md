# SPL 2.0 Cookbook Run Summary — 2026-03-29 Run F (Momagrid, 4-GPU Grid, Laptop Client)

**Date:** 2026-03-29 (evening)
**Adapter:** momagrid (parallel, 10 workers)
**Hub:** http://192.168.0.235:9000 (duck machine, PostgreSQL backend)
**Client:** laptop (not a GPU node — pure task submission, no local inference)
**Status:** **37/37 Success (100%)**
**Total Elapsed:** 403.6s (~6.7 minutes)

---

## Grid Configuration

| Node  | GPU           | VRAM  | Tier   |
|-------|---------------|-------|--------|
| duck  | GTX 1080 Ti   | 11 GB | GOLD   |
| cat   | GTX 1080 Ti   | 11 GB | GOLD   |
| dog   | GTX 1080 Ti   | 11 GB | GOLD   |
| goose | RTX 4060      |  8 GB | SILVER |

**Hub config:** `--max-concurrent 3` per agent → 12 total dispatch slots

**Notable:** recipes submitted from a laptop on the same LAN — client machine has no GPU
and did not join the grid as an agent. Validates the client-only submission workflow.

---

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 6.3s |
| 02 | Ollama Proxy | OK | 4.4s |
| 03 | Multilingual Greeting | OK | 4.3s |
| 04 | Model Showdown | OK | 220.9s |
| 05 | Self-Refine | OK | 16.4s |
| 06 | ReAct Agent | OK | 12.3s |
| 07 | Safe Generation | OK | 38.4s |
| 08 | RAG Query | OK | 4.4s |
| 09 | Chain of Thought | OK | 46.5s |
| 10 | Batch Test | OK | 90.7s |
| 11 | Debate Arena | OK | 114.6s |
| 12 | Plan and Execute | OK | 224.9s |
| 13 | Map-Reduce Summarizer | OK | 14.3s |
| 14 | Multi-Agent Collaboration | OK | 271.0s |
| 15 | Code Review | OK | 82.5s |
| 16 | Reflection Agent | OK | 387.2s |
| 17 | Tree of Thought | OK | 355.1s |
| 18 | Guardrails Pipeline | OK | 44.4s |
| 19 | Memory Conversation | OK | 11.4s |
| 20 | Ensemble Voting | OK | 305.0s |
| 21 | Multi-Model Pipeline | OK | 108.6s |
| 22 | Text2SPL Demo | OK | 239.2s |
| 23 | Structured Output | OK | 14.3s |
| 24 | Few-Shot Prompting | OK | 10.3s |
| 25 | Nested Procedures | OK | 106.5s |
| 26 | Prompt A/B Test | OK | 82.5s |
| 27 | Data Extraction | OK | 4.3s |
| 28 | Customer Support Triage | OK | 168.6s |
| 29 | Meeting Notes to Actions | OK | 36.3s |
| 30 | Code Generator + Tests | OK | 148.6s |
| 31 | Sentiment Pipeline | OK | 34.3s |
| 32 | Socratic Tutor | OK | 98.5s |
| 33 | Interview Simulator | OK | 116.5s |
| 34 | Progressive Summarizer | OK | 58.4s |
| 35 | Hypothesis Tester | OK | 102.5s |
| 36 | Tool-Use / Function-Call | OK | 22.3s |
| 37 | Headline News Aggregator | OK | 70.5s |

**Failures:** 0

---

## Comparison: All Runs

| Date | Label | Client | Adapter | Nodes | Workers | Pass Rate | Wall Clock |
|------|-------|--------|---------|-------|---------|-----------|------------|
| 2026-03-24 | A | duck | ollama | 1 | 1 | 37/37 | 1763.2s |
| 2026-03-25 | A | duck | ollama | 1 | 1 | 37/37 | 1000.0s |
| 2026-03-27 | A | duck | ollama | 1 | 1 | 37/37 | 1197.6s |
| 2026-03-27 | B | duck | momagrid | 2 | 5 | 37/37 | 660.4s |
| 2026-03-27 | C | duck | momagrid | 3 | 10 | 33/37 | 548.6s |
| 2026-03-27 | D | duck | momagrid | 3 | 10 | 33/37 | 383.7s |
| 2026-03-29 | E | duck | momagrid | 4 | 10 | 37/37 ✓ | 414.1s |
| 2026-03-29 | **F** | **laptop** | **momagrid** | **4** | **10** | **37/37 ✓** | **403.6s** |

**Speedup vs single-node sequential (baseline 1493s):** 1493.4s → 403.6s = **3.7×**
**Speedup vs single-node sequential (best 1000s):** 1000.0s → 403.6s = **2.5×**
**vs run E (same grid, hub client):** 414.1s → 403.6s = **10.5s faster** (within thermal variance)

---

## Wall Clock Trend

```
1763s  ████████████████████████████████████  03-24  1-node sequential
1493s  ██████████████████████████████       03-27   1-node sequential (paper baseline)
1197s  ████████████████████████             03-27A  1-node sequential
1000s  ████████████████████                 03-25   1-node sequential (best)
 660s  █████████████                        03-27B  2-node momagrid
 548s  ███████████                          03-27C  3-node momagrid (unbalanced)
 414s  ████████                             03-29E  4-node momagrid, hub client (100% ✓)
 404s  ████████                             03-29F  4-node momagrid, laptop client (100% ✓)
 383s  ████████                             03-27D  3-node momagrid (89.2%)
```

---

## Bottleneck Analysis

Wall clock is again gated by the two longest sequential recipes:

| ID | Recipe | Run E | Run F | Delta |
|----|--------|-------|-------|-------|
| 16 | Reflection Agent | 357.1s | 387.2s | +30.1s |
| 17 | Tree of Thought | 383.2s | 355.1s | -28.1s |

Both runs finish within ~14s of each other despite recipe-level variance of ±30s —
confirming the ~383–414s floor is a scheduling/thermal constant, not noise.

The floor is defined by whichever of these two runs last on its node.
Run F's wall time (403.6s) is consistent with run E (414.1s): **reproduced**.

---

## Reproducibility Verdict

| Metric | Run E | Run F | Verdict |
|--------|-------|-------|---------|
| Pass rate | 37/37 (100%) | 37/37 (100%) | ✓ Reproduced |
| Wall clock | 414.1s | 403.6s | ✓ Within variance (±3%) |
| Failures | 0 | 0 | ✓ Reproduced |
| Client type | hub machine | external laptop | ✓ Client-agnostic |

**The 4-node momagrid grid is stable and reproducible across client machines.**
Submitting from a laptop vs the hub node makes no measurable difference —
the bottleneck is GPU inference time, not submission overhead.

---

## Key Achievement

Run F is the **first submission from an external client machine** (laptop with no GPU).
This validates the AI@Home vision: anyone on the LAN — or eventually the WAN via
`momagrid.org` — can submit workflows without owning a GPU or running an agent.
