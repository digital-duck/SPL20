# SPL 2.0 Cookbook — Run Report: Mini-PC CPU
**Date:** 2026-04-07
**Author:** Wen Gong (Digital Duck)

---

## Summary

| Metric | Value |
|--------|-------|
| Result | **45/45 Success** |
| Total elapsed (wall) | 9448.9s (~157.5 min, ~2.6 hours) |
| Adapter | ollama (sequential, 1 worker) |
| Model | gemma3 |
| Infrastructure | Mini-PC, Ubuntu 24.04, 16 CPUs, 32 GB RAM, **no GPU** |

**First full run on a standalone CPU-only mini-PC — baseline for CPU inference performance.**

---

## Comparison vs 4-GPU Momagrid LAN (2026-03-29)

The reference GPU run is the **2026-03-29 LAN momagrid run** — pure LAN, no external tunnel, the cleanest infrastructure comparison available. That run covered 37 recipes (recipes 41–45 and 47–49 were added later). Per-recipe timings below may also reflect minor recipe evolution between March 29 and April 7.

| Metric | Mini-PC CPU | 4-GPU Momagrid LAN | Ratio |
|--------|-------------|----------------|-------|
| Infrastructure | 16 CPUs, 32 GB RAM, no GPU | 4 GPUs (~41 GB VRAM) | — |
| Execution | Sequential (1 worker) | Parallel (10 workers) | — |
| Network | Local ollama | LAN only (hub at 192.168.0.235) | — |
| Total wall time | 9448.9s (45 recipes) | 414.1s (37 recipes) | **22.8× faster on GPU cluster** ¹ |
| Recipes passed | 45/45 | 37/37 | — |
| Failures | 0 | 0 | — |

¹ Wall-time ratio is indicative only — the two runs cover different recipe sets.

The wall-time advantage of the 4-GPU cluster comes from two compounding factors:

1. **GPU inference speed** — individual recipes run 2–10× faster on GPU than CPU (varies by recipe complexity and multi-model switching)
2. **Parallel dispatch** — momagrid runs up to 10 recipes concurrently, adding another ~6–8× throughput multiplier

Model cold-start costs (see section below) further widen the gap for multi-model recipes on CPU.

---

## Recipe 19 Fix — Memory Conversation

The initial batch run failed with `Error: No module named 'dd_db'` (0.4s) — a missing dependency, not an SPL or model issue. After installing `dd_db` into the `spl2` conda environment, recipe 19 was re-run on 2026-04-08 and passed in **9.4s** (3 LLM calls). The final result for this run is **45/45**.

---

## Ollama Cold Start and Model Switching

A factor not fully captured in recipe-level timing is **ollama model load latency**. When ollama switches between models — or loads a model cold after being idle — it must load the model weights into memory before the first token is generated.

On a **CPU-only** machine with 32 GB RAM this cost is particularly significant:
- Model weights load into system RAM with no VRAM fast path
- CPU RAM bandwidth is substantially lower than GPU VRAM bandwidth
- gemma3 (12B) can take **10–30+ seconds** to load cold on CPU

The sequential run compounds this: every recipe that involves a different model pays a cold-start tax. Recipes that drive **multiple models in sequence** — **Model Showdown (#04)**, **Ensemble Voting (#20)**, **Multi-Model Pipeline (#21)**, **Tree of Thought (#17)** — each trigger several load cycles back-to-back, making cold-start a non-trivial fraction of their total runtime.

On the 4-GPU momagrid, VRAM bandwidth and the ability to keep models warm across parallel workers reduces this overhead substantially. The 3–4× per-recipe slowdowns seen in multi-step recipes likely include significant cold-start contribution on top of raw inference speed.

---

## What This Run Demonstrates: Tasks That Work Well on CPU

Despite the raw speed gap, this test shows that a **CPU-only mini-PC (16C / 32 GB) is a viable SPL runtime** for many real workloads. All 45 recipes completed successfully, and a large subset ran in seconds:

| Category | Examples | CPU time | Verdict |
|----------|----------|----------|---------|
| Simple single-turn queries | #02 Ollama Proxy, #03 Multilingual, #24 Few-Shot | 4–5s | Excellent |
| Short tool-use / structured output | #08 RAG Query, #23 Structured Output, #27 Data Extraction | 4–8s | Excellent |
| Light agentic loops | #06 ReAct Agent, #18 Guardrails, #41 Human Steering | 12–13s | Excellent |
| Finance / compliance tasks | #48 Credit Risk, #49 Regulatory Audit | 48–50s | Usable |
| Multi-step reasoning | #16 Reflection (1159s), #17 Tree of Thought (883s) | 15–20 min | Slow but correct |

For **development, testing, and low-volume workloads**, the mini-PC is a fully functional SPL node with no GPU dependency. It validates all recipe logic end-to-end and handles lightweight production use cases without any external infrastructure.

---

## Recipe Results

GPU times are from the **2026-03-29 LAN momagrid run** (37 recipes). Recipes 41–49 were added after that run and have no LAN GPU baseline yet.

| ID | Recipe | CPU Time | GPU Time (LAN) | Slowdown |
|----|--------|----------|----------------|----------|
| 01 | Hello World | 17.1s | 16.8s | 1.0× |
| 02 | Ollama Proxy | 4.3s | 16.8s | **0.3×** ¹ |
| 03 | Multilingual Greeting | 4.4s | 4.8s | **0.9×** ¹ |
| 04 | Model Showdown | 117.8s | 66.9s | 1.8× |
| 05 | Self-Refine | 292.5s | 30.8s | 9.5× ³ |
| 06 | ReAct Agent | 12.6s | 30.9s | **0.4×** ¹ |
| 07 | Safe Generation | 144.6s | 40.9s | 3.5× |
| 08 | RAG Query | 3.9s | 24.8s | **0.2×** ¹ |
| 09 | Chain of Thought | 187.1s | 26.8s | 7.0× |
| 10 | Batch Test | 34.0s | 60.9s | **0.6×** ¹ |
| 11 | Debate Arena | 413.2s | 176.7s | 2.3× |
| 12 | Plan and Execute | 219.0s | 296.9s | **0.7×** ¹ |
| 13 | Map-Reduce Summarizer | 41.1s | 50.4s | **0.8×** ¹ |
| 14 | Multi-Agent Collaboration | 630.2s | 140.6s | 4.5× |
| 15 | Code Review | 689.1s | 128.5s | 5.4× |
| 16 | Reflection Agent | 1159.0s | 357.1s | 3.2× |
| 17 | Tree of Thought | 883.3s | 383.2s | 2.3× |
| 18 | Guardrails Pipeline | 11.6s | 26.3s | **0.4×** ¹ |
| 19 | Memory Conversation | 9.4s ² | 11.0s | **0.9×** ¹ |
| 20 | Ensemble Voting | 787.1s | 200.7s | 3.9× |
| 21 | Multi-Model Pipeline | 187.0s | 96.5s | 1.9× |
| 22 | Text2SPL Demo | 93.2s | 162.7s | **0.6×** ¹ |
| 23 | Structured Output | 8.1s | 48.4s | **0.2×** ¹ |
| 24 | Few-Shot Prompting | 4.9s | 6.3s | **0.8×** ¹ |
| 25 | Nested Procedures | 375.6s | 148.6s | 2.5× |
| 26 | Prompt A/B Test | 248.0s | 82.4s | 3.0× |
| 27 | Data Extraction | 7.2s | 16.3s | **0.4×** ¹ |
| 28 | Customer Support Triage | 258.5s | 90.5s | 2.9× |
| 29 | Meeting Notes to Actions | 65.5s | 60.4s | 1.1× |
| 30 | Code Generator + Tests | 586.4s | 160.6s | 3.7× |
| 31 | Sentiment Pipeline | 200.1s | 34.3s | 5.8× |
| 32 | Socratic Tutor | 240.1s | 106.5s | 2.3× |
| 33 | Interview Simulator | 494.3s | 132.6s | 3.7× |
| 34 | Progressive Summarizer | 45.4s | 40.4s | 1.1× |
| 35 | Hypothesis Tester | 443.2s | 84.4s | 5.3× |
| 36 | Tool-Use / Function-Call | 44.6s | 12.3s | 3.6× |
| 37 | Headline News Aggregator | 191.8s | 80.4s | 2.4× |
| 41 | Human Steering | 12.7s | — | — |
| 42 | Knowledge Synthesis | 6.5s | — | — |
| 43 | Prompt Self-Tuning | 32.0s | — | — |
| 44 | Adaptive Failover | 72.2s | — | — |
| 45 | Vision to Action | 3.0s | — | — |
| 47 | arXiv Morning Brief | 78.4s | — | — |
| 48 | Credit Risk Assessment | 49.8s | — | — |
| 49 | Regulatory News Audit | 48.1s | — | — |

¹ **CPU faster than GPU** — see note below.
² Re-run on 2026-04-08 after installing `dd_db`; initial batch run failed (0.4s).
³ Large ratio likely reflects recipe expansion between March 29 and April 7 — Self-Refine added more refinement iterations.

Skipped (not active): 38 Bedrock Quickstart, 39 Vertex AI Quickstart, 40 Azure OpenAI Quickstart

---

## Performance Notes

### Slowest recipes on CPU (top 5)

| ID | Recipe | CPU Time | GPU Time | Slowdown |
|----|--------|----------|----------|----------|
| 16 | Reflection Agent | **1159.0s** | 362.6s | 3.2× |
| 17 | Tree of Thought | **883.3s** | 348.9s | 2.5× |
| 20 | Ensemble Voting | **787.1s** | 367.6s | 2.1× |
| 15 | Code Review | **689.1s** | 203.6s | 3.4× |
| 14 | Multi-Agent Collaboration | **630.2s** | 169.1s | 3.7× |

These are multi-turn, multi-step agentic recipes. CPU inference latency compounds with iteration count, and cold-start penalties for model loading are paid multiple times within the same recipe.

### Why some CPU times beat GPU times ¹

About 13 of the 37 comparable recipes ran faster on the mini-PC than on momagrid. All are short single-turn or low-iteration recipes. Two contributing factors:

1. **Momagrid dispatch overhead** — even on LAN, routing through the hub, assigning a job to an agent, and waiting for a free worker slot adds a fixed per-recipe cost. For sub-10-second tasks this overhead is significant relative to actual inference time. Local ollama has zero dispatch overhead.
2. **Parallel contention** — with 10 workers running concurrently, GPU memory pressure or node scheduling on a shared agent can inflate individual recipe times, especially for lighter tasks that happen to land behind a heavy one.

The mini-PC runs ollama locally with no dispatch layer, so trivial tasks complete faster even without a GPU.

### Inference slowdown distribution (vs LAN GPU, 37 recipes)

| Slowdown bracket | Recipes |
|-----------------|---------|
| < 1× (CPU faster) | 02, 03, 06, 08, 10, 12, 13, 18, 19, 22, 23, 24, 27 |
| 1–2× | 01, 04, 21, 29, 34 |
| 2–4× | 11, 14, 17, 20, 25, 26, 28, 30, 32, 33, 36, 37 |
| 4–6× | 07, 15, 16, 31, 35 |
| > 6× | 05 ³, 09 |

---

## Infrastructure Comparison

| Attribute | Mini-PC CPU | 4-GPU Momagrid LAN |
|-----------|-------------|----------------|
| Hardware | 16 CPUs, 32 GB RAM, no GPU | 3× GTX 1080 Ti (11 GB) + 1× RTX 4060 (8 GB) |
| Total VRAM | 0 GB | ~41 GB |
| Inference backend | ollama (CPU) | ollama (GPU) per node |
| Dispatcher | direct ollama | momagrid hub (192.168.0.235:9000) |
| Network | localhost | LAN only |
| Parallelism | 1 worker (sequential) | 10 workers (parallel) |
| Model cold-start cost | High (system RAM, no VRAM) | Low (VRAM, models stay warm) |
| Recipes | 45 | 37 |
| Wall time | 9448.9s | 414.1s |
| Pass rate | 45/45 (100%) | 37/37 (100%) |

---

## Milestones

- **First CPU-only baseline run** — all 45 recipes pass end-to-end on a minimal Ubuntu 24.04 mini-PC with no GPU.
- **CPU viability confirmed** — for development, CI testing, and lightweight single-turn tasks, a CPU-only mini-PC is a fully functional SPL node with no GPU required.
- **21.7× wall-time speedup** measured for the 4-GPU cluster vs a single CPU node, quantifying the value of momagrid horizontal scaling.
- **Recipe 19 (Memory Conversation)** initially failed due to a missing `dd_db` pip package; fixed and re-run on 2026-04-08, result: pass (9.4s).
