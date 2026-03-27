# SPL20 Cookbook Run Summary — 2026-03-27-C (Momagrid, 3-GPU Grid)

**Machine:** Momagrid grid — 3 nodes (ducklover1 + dog + cat)
**Adapter:** momagrid (parallel, 10 workers)
**Status:** 33/37 Success
**Total Elapsed:** 548.6s (~9 minutes)

---

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 8.5s |
| 02 | Ollama Proxy | OK | 12.8s |
| 03 | Multilingual Greeting | OK | 4.4s |
| 04 | Model Showdown | OK | 92.4s |
| 05 | Self-Refine | OK | 33.1s |
| 06 | ReAct Agent | OK | 29.1s |
| 07 | Safe Generation | OK | 59.9s |
| 08 | RAG Query | OK | 10.8s |
| 09 | Chain of Thought | OK | 35.1s |
| 10 | Batch Test | OK | 100.8s |
| 11 | Debate Arena | **FAILED** | 110.0s |
| 12 | Plan and Execute | OK | 493.4s |
| 13 | Map-Reduce Summarizer | OK | 65.4s |
| 14 | Multi-Agent Collaboration | **FAILED** | 104.7s |
| 15 | Code Review | **FAILED** | 84.9s |
| 16 | Reflection Agent | OK | 431.0s |
| 17 | Tree of Thought | OK | 479.4s |
| 18 | Guardrails Pipeline | OK | 62.0s |
| 19 | Memory Conversation | OK | 40.5s |
| 20 | Ensemble Voting | OK | 390.2s |
| 21 | Multi-Model Pipeline | OK | 95.2s |
| 22 | Text2SPL Demo | OK | 106.9s |
| 23 | Structured Output | **FAILED** | 2.3s |
| 24 | Few-Shot Prompting | OK | 4.4s |
| 25 | Nested Procedures | OK | 131.2s |
| 26 | Prompt A/B Test | OK | 74.4s |
| 27 | Data Extraction | OK | 8.5s |
| 28 | Customer Support Triage | OK | 198.9s |
| 29 | Meeting Notes to Actions | OK | 78.2s |
| 30 | Code Generator + Tests | OK | 231.8s |
| 31 | Sentiment Pipeline | OK | 99.0s |
| 32 | Socratic Tutor | OK | 338.1s |
| 33 | Interview Simulator | OK | 268.6s |
| 34 | Progressive Summarizer | OK | 186.4s |
| 35 | Hypothesis Tester | OK | 178.8s |
| 36 | Tool-Use / Function-Call | OK | 47.4s |
| 37 | Headline News Aggregator | OK | 180.5s |

---

## Failure Analysis

All 4 failures share the same root cause: **Ollama not reachable on an agent node**.

| ID | Recipe | Error |
|----|--------|-------|
| 11 | Debate Arena | `dial tcp 127.0.0.1:11434: connect: connection refused` |
| 14 | Multi-Agent Collaboration | `EOF` (connection dropped mid-request) |
| 15 | Code Review | `dial tcp 127.0.0.1:11434: connect: connection refused` |
| 23 | Structured Output | `dial tcp 127.0.0.1:11434: connect: connection refused` |

**Root cause:** The hub dispatched tasks to an agent node (likely `cat`, the newest node) whose Ollama instance was not running or crashed under load. The momagrid agent registered as ONLINE but Ollama on `localhost:11434` was not available on that node.

**Fix:** Before running, verify Ollama is running on all agent nodes:
```bash
curl http://<agent-ip>:11434/api/tags   # on each node
# or
ollama list                              # on each node
```

**Observation:** `cat` was showing idle (0 tasks) while `duck` and `dog` were saturated — consistent with the hub detecting Ollama failures on `cat` and stopping dispatch to it mid-run.

---

## Comparison: All Runs

| Date | Label | Adapter | Mode | Nodes | Workers | Pass Rate | Wall Clock |
|------|-------|---------|------|-------|---------|-----------|------------|
| 2026-03-24 | A | ollama | sequential | 1 | 1 | 37/37 | 1763.2s |
| 2026-03-25 | A | ollama | sequential | 1 | 1 | 37/37 | 1000.0s |
| 2026-03-27 | A | ollama | sequential | 1 | 1 | 37/37 | 1197.6s |
| 2026-03-27 | B | momagrid | parallel | 2 | 5 | 37/37* | 660.4s |
| 2026-03-27 | **C** | **momagrid** | **parallel** | **3** | **10** | **33/37** | **548.6s** |

*\* Run B had 1 pre-fix failure (#06), effectively 37/37 after fix.*

**Speedup vs sequential (same day):** 1197.6s → 548.6s = **2.2x faster**
**Speedup vs Run B (2 nodes):** 660.4s → 548.6s = **1.2x faster** (3rd node added ~17% improvement despite failures)

---

## Wall Clock Trend

```
1763s  ████████████████████████████████████  03-24  1-node sequential
1197s  ████████████████████████             03-27A  1-node sequential
1000s  ████████████████████                 03-25   1-node sequential
 660s  █████████████                        03-27B  2-node momagrid
 548s  ███████████                          03-27C  3-node momagrid (4 failures)
```

---

## Bottleneck Analysis

With 3 nodes, the wall clock ceiling is now the slowest single recipe:

| ID | Recipe | Elapsed | Note |
|----|--------|---------|------|
| 12 | Plan and Execute | 493.4s | Multi-step planning, inherently sequential |
| 17 | Tree of Thought | 479.4s | 3-model branching |
| 16 | Reflection Agent | 431.0s | Iterative self-critique |
| 20 | Ensemble Voting | 390.2s | Multiple parallel votes |

These are long-running single-task recipes — they cannot be further parallelized by adding nodes. The floor for wall clock time with current recipes is approximately **~500s** unless these recipes are internally parallelized.

---

## Next Steps

1. **Fix `cat` node** — ensure Ollama is running before joining hub (`systemctl status ollama` or `ollama serve`)
2. **Rerun with 3 healthy nodes** — expect ~500s wall clock and 37/37 if cat is stable
3. **Node 4** arriving 2026-03-30 — will add another GPU but won't reduce wall clock below ~500s ceiling
4. **Internal parallelization** of long-running recipes (#12, #16, #17, #20) is the next optimization frontier
