# SPL20 Cookbook Run Summary — 2026-03-27

**Machine:** Ubuntu (papa-game)
**Status:** 37/37 Success
**Total Elapsed:** 1197.6s (~20 minutes)

## Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 1.3s |
| 02 | Ollama Proxy | OK | 0.7s |
| 03 | Multilingual Greeting | OK | 3.1s |
| 04 | Model Showdown | OK | 34.3s |
| 05 | Self-Refine | OK | 4.5s |
| 06 | ReAct Agent | OK | 37.1s |
| 07 | Safe Generation | OK | 12.1s |
| 08 | RAG Query | OK | 1.0s |
| 09 | Chain of Thought | OK | 18.9s |
| 10 | Batch Test | OK | 8.0s |
| 11 | Debate Arena | OK | 48.8s |
| 12 | Plan and Execute | OK | 17.0s |
| 13 | Map-Reduce Summarizer | OK | 10.1s |
| 14 | Multi-Agent Collaboration | OK | 87.0s |
| 15 | Code Review | OK | 39.4s |
| 16 | Reflection Agent | OK | 154.0s |
| 17 | Tree of Thought | OK | 191.6s |
| 18 | Guardrails Pipeline | OK | 5.5s |
| 19 | Memory Conversation | OK | 1.9s |
| 20 | Ensemble Voting | OK | 36.5s |
| 21 | Multi-Model Pipeline | OK | 35.6s |
| 22 | Text2SPL Demo | OK | 27.4s |
| 23 | Structured Output | OK | 1.4s |
| 24 | Few-Shot Prompting | OK | 0.7s |
| 25 | Nested Procedures | OK | 31.9s |
| 26 | Prompt A/B Test | OK | 23.2s |
| 27 | Data Extraction | OK | 1.6s |
| 28 | Customer Support Triage | OK | 46.2s |
| 29 | Meeting Notes to Actions | OK | 12.3s |
| 30 | Code Generator + Tests | OK | 65.3s |
| 31 | Sentiment Pipeline | OK | 13.6s |
| 32 | Socratic Tutor | OK | 26.2s |
| 33 | Interview Simulator | OK | 78.6s |
| 34 | Progressive Summarizer | OK | 24.5s |
| 35 | Hypothesis Tester | OK | 40.2s |
| 36 | Tool-Use / Function-Call | OK | 8.2s |
| 37 | Headline News Aggregator | OK | 47.9s |

## Notes

- All 37 cookbook recipes passed on this Ubuntu machine (papa-game).
- Slowest recipes: Tree of Thought (191.6s), Reflection Agent (154.0s), Multi-Agent Collaboration (87.0s).
- Fastest recipes: Few-Shot Prompting (0.7s), Ollama Proxy (0.7s), RAG Query (1.0s).
- Average elapsed per recipe: ~32.4s.

---

## Comparison with Prior Runs

### Overall Performance

| Date | Pass Rate | Total Time | Delta vs Prior |
|------|-----------|------------|----------------|
| 2026-03-24 | 37/37 | 1763.2s | +384.4s (fixed #18 Guardrails) |
| 2026-03-25 | 37/37 | 1000.0s | **-763.2s (-43.3%)** |
| 2026-03-27 | 37/37 | **1197.6s** | +197.6s (+19.8%) |

### Key Observations

**Pass rate:** Stable at 37/37 for all three runs. The only prior failure (#18 Guardrails, 03-23) has stayed fixed.

**Runtime trend:** 03-24 was an outlier high (plan+execute spiked to 508.5s alone). 03-25 snapped back to ~1000s. Today's 1197.6s is a modest regression vs 03-25 but still well below 03-24.

**Per-recipe comparison (where data exists):**

| ID | Recipe | 03-24 | 03-27 | Delta |
|----|--------|-------|-------|-------|
| 12 | Plan and Execute | 508.5s | 17.0s | **-491.5s** (back to normal) |
| 16 | Reflection Agent | 158.1s | 154.0s | -4.1s |
| 33 | Interview Simulator | 173.6s | 78.6s | -95.0s |
| 14 | Multi-Agent Collaboration | 74.8s | 87.0s | +12.2s |

**Today's slow outliers** driving the +197.6s vs 03-25:
- #17 Tree of Thought: 191.6s (uses 3 different models — expected to be slow)
- #16 Reflection Agent: 154.0s
- #14 Multi-Agent Collaboration: 87.0s

**Bottom line:** Today's run is healthy — all 37 pass, runtime is between the 03-25 low and 03-24 spike. The variance is consistent with LLM response latency fluctuation on multi-agent/reflection-heavy recipes.
