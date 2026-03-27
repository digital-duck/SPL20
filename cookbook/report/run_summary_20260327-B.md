# SPL20 Cookbook Run Summary — 2026-03-27-B (Momagrid, 2-GPU Grid)

**Machine:** Momagrid grid — 2 nodes (ducklover1 + dog)
**Adapter:** momagrid (parallel, 5 workers)
**Status:** 36/37 Success *(#06 ReAct Agent pre-fix failure — rerun confirmed OK in 8.5s)*
**Effective:** 37/37 with fix applied
**Total Elapsed:** 660.4s (~11 minutes)

---

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 4.4s |
| 02 | Ollama Proxy | OK | 4.4s |
| 03 | Multilingual Greeting | OK | 4.4s |
| 04 | Model Showdown | OK | 59.6s |
| 05 | Self-Refine | OK | 13.6s |
| 06 | ReAct Agent | FAILED* | 0.2s |
| 07 | Safe Generation | OK | 59.6s |
| 08 | RAG Query | OK | 4.4s |
| 09 | Chain of Thought | OK | 67.6s |
| 10 | Batch Test | OK | 51.2s |
| 11 | Debate Arena | OK | 108.6s |
| 12 | Plan and Execute | OK | 184.7s |
| 13 | Map-Reduce Summarizer | OK | 33.0s |
| 14 | Multi-Agent Collaboration | OK | 149.9s |
| 15 | Code Review | OK | 184.7s |
| 16 | Reflection Agent | OK | 352.3s |
| 17 | Tree of Thought | OK | 348.2s |
| 18 | Guardrails Pipeline | OK | 43.4s |
| 19 | Memory Conversation | OK | 11.6s |
| 20 | Ensemble Voting | OK | 225.7s |
| 21 | Multi-Model Pipeline | OK | 106.8s |
| 22 | Text2SPL Demo | OK | 75.8s |
| 23 | Structured Output | OK | 4.3s |
| 24 | Few-Shot Prompting | OK | 4.4s |
| 25 | Nested Procedures | OK | 86.3s |
| 26 | Prompt A/B Test | OK | 121.0s |
| 27 | Data Extraction | OK | 20.7s |
| 28 | Customer Support Triage | OK | 63.8s |
| 29 | Meeting Notes to Actions | OK | 41.3s |
| 30 | Code Generator + Tests | OK | 148.1s |
| 31 | Sentiment Pipeline | OK | 63.8s |
| 32 | Socratic Tutor | OK | 80.2s |
| 33 | Interview Simulator | OK | 168.2s |
| 34 | Progressive Summarizer | OK | 69.9s |
| 35 | Hypothesis Tester | OK | 115.0s |
| 36 | Tool-Use / Function-Call | OK | 18.7s |
| 37 | Headline News Aggregator | OK | 59.8s |

*\* #06 ReAct Agent failed due to `allowed_tools` kwarg not accepted by MomagridAdapter — fixed in `spl/adapters/__init__.py`. Rerun: OK (8.5s).*

---

## Comparison: All Runs

| Date | Label | Adapter | Mode | Nodes | Pass Rate | Wall Clock |
|------|-------|---------|------|-------|-----------|------------|
| 2026-03-24 | A | ollama | sequential | 1 | 37/37 | 1763.2s |
| 2026-03-25 | A | ollama | sequential | 1 | 37/37 | 1000.0s |
| 2026-03-27 | A | ollama | sequential | 1 | 37/37 | 1197.6s |
| 2026-03-27 | **B** | **momagrid** | **parallel (5 workers)** | **2** | **37/37** | **660.4s** |

**Speedup vs same-day sequential:** 1197.6s → 660.4s = **~1.8x faster**
**Speedup vs best sequential (03-25):** 1000.0s → 660.4s = **~1.5x faster**

---

## Per-Recipe Comparison: Sequential vs Momagrid

| ID | Recipe | 03-27 Sequential | 03-27 Momagrid | Delta |
|----|--------|-----------------|----------------|-------|
| 04 | Model Showdown | 34.3s | 59.6s | +25.3s |
| 09 | Chain of Thought | 18.9s | 67.6s | +48.7s |
| 11 | Debate Arena | 48.8s | 108.6s | +59.8s |
| 12 | Plan and Execute | 17.0s | 184.7s | +167.7s |
| 14 | Multi-Agent Collaboration | 87.0s | 149.9s | +62.9s |
| 15 | Code Review | 39.4s | 184.7s | +145.3s |
| 16 | Reflection Agent | 154.0s | 352.3s | +198.3s |
| 17 | Tree of Thought | 191.6s | 348.2s | +156.6s |
| 20 | Ensemble Voting | 36.5s | 225.7s | +189.2s |
| 26 | Prompt A/B Test | 23.2s | 121.0s | +97.8s |
| 33 | Interview Simulator | 78.6s | 168.2s | +89.6s |

**Note:** Individual recipe elapsed times are longer under momagrid because tasks queue at the hub and wait for an agent slot. The wall clock wins come from parallelism — many recipes run simultaneously rather than one-by-one.

---

## GPU Utilisation (Agent Node: dog / papa-game)

- **GPU:** NVIDIA GeForce GTX 1080 Ti (11264 MiB VRAM)
- **GPU-Util:** 88% during run
- **Power:** 238W / 280W capacity
- **VRAM in use:** ~7.6 GB (two concurrent Ollama processes: 2804 + 4786 MiB)

Both GPUs (ducklover1 + dog) were actively dispatched tasks by the hub.

---

## Bug Fixed This Run

**#06 ReAct Agent — `allowed_tools` kwarg rejected by MomagridAdapter**

- **Root cause:** `spl/adapters/__init__.py` `get_adapter()` passed all CLI kwargs blindly to the adapter constructor. `--allowed-tools WebSearch` is claude_cli-specific and not accepted by MomagridAdapter.
- **Fix:** `get_adapter()` now inspects each adapter's `__init__` signature and silently drops unsupported kwargs before instantiation.
- **Result:** Recipe #06 rerun with `--ids 06 --adapter momagrid` → OK (8.5s).

---

## Notes

- Wall clock speedup is driven by parallel submission — 5 workers keep the hub queue saturated across both GPUs.
- Bottleneck is now the slowest sequential recipe (#16 Reflection Agent: 352.3s, #17 Tree of Thought: 348.2s) — these are the ceiling until more nodes join.
- Node 4 (GTX 1080 Ti) arriving 2026-03-30. Node 5 pending Ubuntu re-image. With 3+ nodes the ceiling should drop further.
- Average per-recipe elapsed (momagrid): ~88s vs ~32s sequential — expected, since parallel recipes queue at hub. What matters is wall clock.
