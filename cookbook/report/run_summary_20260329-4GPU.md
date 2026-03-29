# SPL 2.0 Cookbook Run Summary — 2026-03-29 (Momagrid, 4-GPU Grid)

**Date:** 2026-03-29 15:30–16:17 EDT
**Adapter:** momagrid (parallel, 10 workers)
**Hub:** http://192.168.0.235:9000 (duck machine, PostgreSQL backend)
**Status:** **37/37 Success (100%)**
**Total Elapsed:** 414.1s (~6.9 minutes)

---

## Grid Configuration

| Node  | GPU           | VRAM  | Tier   | Agent ID     |
|-------|---------------|-------|--------|--------------|
| duck  | GTX 1080 Ti   | 11 GB | GOLD   | agent-3c5d1413 |
| cat   | GTX 1080 Ti   | 11 GB | GOLD   | agent-807f41d1 |
| dog   | GTX 1080 Ti   | 11 GB | GOLD   | agent-8d5892da |
| goose | RTX 4060      |  8 GB | SILVER | agent-da635fe4 |

**Hub config:** `--max-concurrent 3` per agent → 12 total dispatch slots

---

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 16.8s |
| 02 | Ollama Proxy | OK | 16.8s |
| 03 | Multilingual Greeting | OK | 4.8s |
| 04 | Model Showdown | OK | 66.9s |
| 05 | Self-Refine | OK | 30.8s |
| 06 | ReAct Agent | OK | 30.9s |
| 07 | Safe Generation | OK | 40.9s |
| 08 | RAG Query | OK | 24.8s |
| 09 | Chain of Thought | OK | 26.8s |
| 10 | Batch Test | OK | 60.9s |
| 11 | Debate Arena | OK | 176.7s |
| 12 | Plan and Execute | OK | 296.9s |
| 13 | Map-Reduce Summarizer | OK | 50.4s |
| 14 | Multi-Agent Collaboration | OK | 140.6s |
| 15 | Code Review | OK | 128.5s |
| 16 | Reflection Agent | OK | 357.1s |
| 17 | Tree of Thought | OK | 383.2s |
| 18 | Guardrails Pipeline | OK | 26.3s |
| 19 | Memory Conversation | OK | 11.0s |
| 20 | Ensemble Voting | OK | 200.7s |
| 21 | Multi-Model Pipeline | OK | 96.5s |
| 22 | Text2SPL Demo | OK | 162.7s |
| 23 | Structured Output | OK | 48.4s |
| 24 | Few-Shot Prompting | OK | 6.3s |
| 25 | Nested Procedures | OK | 148.6s |
| 26 | Prompt A/B Test | OK | 82.4s |
| 27 | Data Extraction | OK | 16.3s |
| 28 | Customer Support Triage | OK | 90.5s |
| 29 | Meeting Notes to Actions | OK | 60.4s |
| 30 | Code Generator + Tests | OK | 160.6s |
| 31 | Sentiment Pipeline | OK | 34.3s |
| 32 | Socratic Tutor | OK | 106.5s |
| 33 | Interview Simulator | OK | 132.6s |
| 34 | Progressive Summarizer | OK | 40.4s |
| 35 | Hypothesis Tester | OK | 84.4s |
| 36 | Tool-Use / Function-Call | OK | 12.3s |
| 37 | Headline News Aggregator | OK | 80.4s |

**Failures:** 0

---

## Comparison: All Runs

| Date | Label | Adapter | Mode | Nodes | Workers | Pass Rate | Wall Clock |
|------|-------|---------|------|-------|---------|-----------|------------|
| 2026-03-24 | A | ollama | sequential | 1 | 1 | 37/37 | 1763.2s |
| 2026-03-25 | A | ollama | sequential | 1 | 1 | 37/37 | 1000.0s |
| 2026-03-27 | A | ollama | sequential | 1 | 1 | 37/37 | 1197.6s |
| 2026-03-27 | B | momagrid | parallel | 2 | 5 | 37/37 | 660.4s |
| 2026-03-27 | C | momagrid | parallel | 3 | 10 | 33/37 | 548.6s |
| 2026-03-27 | **D** | **momagrid** | **parallel** | **3** | **10** | **33/37** | **383.7s** |
| 2026-03-29 | **E** | **momagrid** | **parallel** | **4** | **10** | **37/37 ✓** | **414.1s** |

**Speedup vs single-node sequential (best 1000s):** 1000.0s → 414.1s = **2.4×**
**Speedup vs single-node sequential (baseline 1493s):** 1493.4s → 414.1s = **3.6×**
**vs 3-node run D:** wall time comparable (383.7s → 414.1s, within thermal variance); **success rate 89.2% → 100%**

---

## Wall Clock Trend

```
1763s  ████████████████████████████████████  03-24  1-node sequential
1493s  ██████████████████████████████       03-27   1-node sequential (paper baseline)
1197s  ████████████████████████             03-27A  1-node sequential
1000s  ████████████████████                 03-25   1-node sequential (best)
 660s  █████████████                        03-27B  2-node momagrid
 548s  ███████████                          03-27C  3-node momagrid (unbalanced)
 414s  ████████                             03-29E  4-node momagrid (100% ✓)
 383s  ████████                             03-27D  3-node momagrid (89.2%)
```

---

## Bottleneck Analysis

Wall clock is gated by the two longest single-recipe chains — both irreducibly sequential:

| ID | Recipe | Elapsed | Note |
|----|--------|---------|------|
| 17 | Tree of Thought | 383.2s | 3-branch reasoning tree, inherently sequential |
| 16 | Reflection Agent | 357.1s | Deep meta-cognition loop |

These define a ~383s floor regardless of node count. The 414s wall time (31s above that floor)
reflects scheduler overhead and goose picking up the tail tasks as GOLD nodes drained.

**To break the floor:** internal parallelization of multi-branch recipes (Tree of Thought,
Ensemble Voting) is the next frontier — this requires the SPL optimizer to detect
independent GENERATE branches and dispatch them concurrently.

---

## Tier-Routing Observation

With `--max-concurrent 3` and 3 GOLD nodes (9 GOLD slots), goose (SILVER) only received
work when all 9 GOLD slots were busy. In practice goose handled ~2–3 tasks total for this run.

**To increase SILVER participation:** either promote goose to GOLD (since RTX 4060
performance is comparable to GTX 1080 Ti for 7B models) or increase `--max-concurrent`
to 5 (giving 20 total slots, triggering SILVER earlier).

---

## Key Achievement

The 4-node run is the **first 100% success run on the momagrid adapter** across all 37
active recipes. The 3-node run D achieved 383.7s but had 4 failures (EOF/connection-refused
under peak load). Adding the 4th node distributed thermal load across 4 GPUs instead of 3,
eliminating the Ollama drops that caused those failures.

---

## Fixes Applied (2026-03-29)

| Fix | Component | Description |
|-----|-----------|-------------|
| `llama3.2` baseline check | `momagrid/internal/cli/join.go` | Accept any `llama3.2:*` variant (was only matching `llama3.2:latest`) |
| igrid config fallback | `SPL20/spl/adapters/momagrid.py` | Read hub URL from `~/.igrid/config.yaml` when `MOMAGRID_HUB_URL` not set |
| Cookbook script | `SPL20/cookbook/run_cookbook_on_momagrid.sh` | Updated hub IP from 192.168.0.184 → 192.168.0.235 |
| README docs | `SPL20/cookbook/README.md` | Hub URL resolution chain + tier-routing tuning guide |
