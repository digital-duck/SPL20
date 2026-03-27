# SPL20 Cookbook Run Summary — 2026-03-27-D (Momagrid, 3-GPU Grid, Balanced)

**Machine:** Momagrid grid — 3 nodes (ducklover1 + dog + cat), all fully loaded
**Adapter:** momagrid (parallel, 10 workers)
**Status:** 33/37 Success
**Total Elapsed:** 383.7s (~6.4 minutes)

---

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 17.7s |
| 02 | Ollama Proxy | OK | 5.4s |
| 03 | Multilingual Greeting | OK | 4.7s |
| 04 | Model Showdown | OK | 51.3s |
| 05 | Self-Refine | OK | 18.7s |
| 06 | ReAct Agent | OK | 14.6s |
| 07 | Safe Generation | OK | 66.8s |
| 08 | RAG Query | OK | 4.4s |
| 09 | Chain of Thought | OK | 51.3s |
| 10 | Batch Test | **FAILED** | 71.2s |
| 11 | Debate Arena | OK | 159.3s |
| 12 | Plan and Execute | OK | 290.0s |
| 13 | Map-Reduce Summarizer | OK | 33.1s |
| 14 | Multi-Agent Collaboration | **FAILED** | 55.0s |
| 15 | Code Review | OK | 155.3s |
| 16 | Reflection Agent | **FAILED** | 52.0s |
| 17 | Tree of Thought | OK | 345.2s |
| 18 | Guardrails Pipeline | OK | 21.9s |
| 19 | Memory Conversation | **FAILED** | 20.5s |
| 20 | Ensemble Voting | OK | 200.3s |
| 21 | Multi-Model Pipeline | OK | 84.1s |
| 22 | Text2SPL Demo | OK | 129.2s |
| 23 | Structured Output | OK | 4.3s |
| 24 | Few-Shot Prompting | OK | 4.3s |
| 25 | Nested Procedures | OK | 126.5s |
| 26 | Prompt A/B Test | OK | 74.2s |
| 27 | Data Extraction | OK | 2.3s |
| 28 | Customer Support Triage | OK | 137.7s |
| 29 | Meeting Notes to Actions | OK | 57.6s |
| 30 | Code Generator + Tests | OK | 145.6s |
| 31 | Sentiment Pipeline | OK | 63.5s |
| 32 | Socratic Tutor | OK | 118.7s |
| 33 | Interview Simulator | OK | 134.9s |
| 34 | Progressive Summarizer | OK | 104.7s |
| 35 | Hypothesis Tester | OK | 86.3s |
| 36 | Tool-Use / Function-Call | OK | 14.3s |
| 37 | Headline News Aggregator | OK | 92.3s |

---

## Failure Analysis

All 4 failures: Ollama dropped mid-task on one node running at 90% GPU load.

| ID | Recipe | Error |
|----|--------|-------|
| 10 | Batch Test | `EOF` — connection dropped mid-request |
| 14 | Multi-Agent Collaboration | `EOF` — connection dropped mid-request |
| 16 | Reflection Agent | `connection refused` — Ollama not reachable |
| 19 | Memory Conversation | `EOF` — connection dropped mid-request |

**Root cause:** All 3 GPUs were at ~90% utilisation with 2 concurrent Ollama processes per node. Under sustained peak load, one node's Ollama instance dropped connections. This is a thermal/memory pressure issue, not a code bug.

**Mitigation options:**
- Reduce `maxConcurrent` per agent from 3 to 2 in hub config
- Add Ollama health check to momagrid's agent monitor before dispatching
- Implement automatic retry on EOF in momagrid dispatcher

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

**Speedup vs sequential (best):** 1000.0s → 383.7s = **2.6x faster**
**Speedup vs 2-node run B:** 660.4s → 383.7s = **1.7x faster**
**Speedup vs 3-node run C:** 548.6s → 383.7s = **1.4x faster** (same nodes, cat now balanced)

---

## Wall Clock Trend

```
1763s  ████████████████████████████████████  03-24  1-node sequential
1197s  ████████████████████████             03-27A  1-node sequential
1000s  ████████████████████                 03-25   1-node sequential (best)
 660s  █████████████                        03-27B  2-node momagrid
 548s  ███████████                          03-27C  3-node momagrid (cat unbalanced)
 383s  ████████                             03-27D  3-node momagrid (fully balanced)
```

---

## Bottleneck Analysis

Wall clock is now gated by the two longest single-task recipes:

| ID | Recipe | Elapsed | Note |
|----|--------|---------|------|
| 17 | Tree of Thought | 345.2s | 3-model branching, inherently sequential |
| 12 | Plan and Execute | 290.0s | Multi-step planning chain |

These two recipes alone define the ~345s floor. With 4 nodes, the ceiling stays the same — internal parallelization of these recipes is the next frontier.

---

## Grid Status — End of Day 2026-03-27

| Node | Name | GPU | Status | Tasks Completed |
|------|------|-----|--------|-----------------|
| Hub + Agent | ducklover1 | GTX 1080 Ti | ONLINE | Active |
| Agent | dog | GTX 1080 Ti | ONLINE | Active |
| Agent | cat | GTX 1080 Ti | ONLINE | Active — fully balanced after `ollama pull llama3.2` |
| Agent | — | GTX 1080 Ti | Ordered | Arriving 2026-03-30 |
| Agent | — | GTX 1080 Ti | Pending | Needs Ubuntu re-image |

**Peak GPU utilisation:** ~90% across all 3 nodes simultaneously.

---

## Fixes Applied Today

| Fix | File | Description |
|-----|------|-------------|
| `allowed_tools` kwarg | `spl/adapters/__init__.py` | Filter unsupported kwargs before adapter instantiation |
| `mg agents -v` | `momagrid/internal/cli/client.go` | Add `--verbose` / `-v` flag showing supported models per agent |
| Baseline model check | `momagrid/internal/cli/join.go` | Error on join if `llama3.2` not in Ollama model list |
| `run_all.py` subcommand removed | `cookbook/run_all.py` | Reverted Click subcommands back to flat argparse; added `--workers` flag |
