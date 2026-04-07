# SPL 2.0 Cookbook — Daily Run Report
**Date:** 2026-04-06
**Author:** Wen Gong (Digital Duck)

---

## Summary

| Metric | Value |
|--------|-------|
| Result | **45/45 Success** |
| Total elapsed (wall) | 434.6s (~7.2 min) |
| Adapter | momagrid (parallel, 10 workers) |
| Model | gemma3 |
| Hub URL | https://qgzqm-99-111-153-200.run.pinggy-free.link (public Pinggy) |
| Infrastructure | LAN momagrid — 4 GPUs (3x GTX 1080 Ti 11GB, 1x RTX 4060 8GB) |

**First successful test of momagrid over a public internet URL via Pinggy.**

---

## Recipe Results

| ID | Recipe | Status | Elapsed |
|----|--------|--------|---------|
| 01 | Hello World | OK | 9.3s |
| 02 | Ollama Proxy | OK | 20.8s |
| 03 | Multilingual Greeting | OK | 14.3s |
| 04 | Model Showdown | OK | 43.2s |
| 05 | Self-Refine | OK | 197.0s |
| 06 | ReAct Agent | OK | 36.4s |
| 07 | Safe Generation | OK | 55.8s |
| 08 | RAG Query | OK | 11.5s |
| 09 | Chain of Thought | OK | 47.1s |
| 10 | Batch Test | OK | 34.3s |
| 11 | Debate Arena | OK | 144.7s |
| 12 | Plan and Execute | OK | 275.4s |
| 13 | Map-Reduce Summarizer | OK | 37.3s |
| 14 | Multi-Agent Collaboration | OK | 169.1s |
| 15 | Code Review | OK | 203.6s |
| 16 | Reflection Agent | OK | 362.6s |
| 17 | Tree of Thought | OK | 348.9s |
| 18 | Guardrails Pipeline | OK | 61.1s |
| 19 | Memory Conversation | OK | 23.4s |
| 20 | Ensemble Voting | OK | 367.6s |
| 21 | Multi-Model Pipeline | OK | 114.3s |
| 22 | Text2SPL Demo | OK | 60.6s |
| 23 | Structured Output | OK | 17.6s |
| 24 | Few-Shot Prompting | OK | 8.7s |
| 25 | Nested Procedures | OK | 105.8s |
| 26 | Prompt A/B Test | OK | 122.7s |
| 27 | Data Extraction | OK | 6.2s |
| 28 | Customer Support Triage | OK | 101.2s |
| 29 | Meeting Notes to Actions | OK | 23.6s |
| 30 | Code Generator + Tests | OK | 129.0s |
| 31 | Sentiment Pipeline | OK | 81.4s |
| 32 | Socratic Tutor | OK | 77.1s |
| 33 | Interview Simulator | OK | 157.2s |
| 34 | Progressive Summarizer | OK | 65.2s |
| 35 | Hypothesis Tester | OK | 114.5s |
| 36 | Tool-Use / Function-Call | OK | 13.1s |
| 37 | Headline News Aggregator | OK | 80.7s |
| 41 | Human Steering | OK | 22.5s |
| 42 | Knowledge Synthesis | OK | 13.1s |
| 43 | Prompt Self-Tuning | OK | 46.8s |
| 44 | Adaptive Failover | OK | 19.4s |
| 45 | Vision to Action | OK | 3.7s |
| 47 | arXiv Morning Brief | OK | 20.3s |
| 48 | Credit Risk Assessment | OK | 30.4s |
| 49 | Regulatory News Audit | OK | 72.0s |

Skipped (not active): 38 Bedrock Quickstart, 39 Vertex AI Quickstart, 40 Azure OpenAI Quickstart

---

## Momagrid Agent Inventory

| Agent | Name | Host | GPU | VRAM | Tier | Status |
|-------|------|------|-----|------|------|--------|
| agent-7eefa739 | dog | 192.168.0.170 | GTX 1080 Ti | 11 GB | GOLD | ONLINE |
| agent-c1701dd7 | cat | 192.168.0.184 | GTX 1080 Ti | 11 GB | GOLD | ONLINE |
| agent-389e5488 | duck | 192.168.0.177 | GTX 1080 Ti | 11 GB | GOLD | ONLINE |
| agent-6a5e4a9b | goose | 192.168.0.235 | RTX 4060 | 8 GB | SILVER | ONLINE |

**Total VRAM:** ~41 GB across 4 GPUs. Operator: `duck`.

Notable model coverage per agent:
- **dog:** gemma4, qwen3.5, phi4, deepseek-r1, lfm2.5-thinking, qwen3-embedding
- **cat:** phi4, qwen2.5, deepseek-r1, mathstral, mistral, multiple embedding models
- **duck:** gemma3:12b, phi4, qwen3.5, mathstral, qwen3-embedding
- **goose (SILVER):** deepseek-r1, starcoder2, duckdb-nsql, qwen3-embedding:4b, phi4-mini, snowflake-arctic-embed2

---

## Bug Fixes Applied Today

### Recipe 17 — Tree of Thought (and Recipe 04 — Model Showdown)

**Root cause:** `len(@models)` was calling `_builtin_len()` which estimates token count
(`len(text) // 4`), not list length. For `["gemma3", "phi4", "qwen2.5"]` (30-char JSON
string), this returned `7` instead of `3`.

**Impact on Recipe 17 (prior run):**
- WHILE loop ran 7 iterations instead of 3
- Iterations 4–7 used empty model names, generating extra momagrid tasks
- GPU memory exhaustion → `ollama 500: model runner has unexpectedly stopped`

**Fix:** `len(@models)` → `COUNT(@models)` in both affected SPL files.
`COUNT()` correctly parses the JSON array and returns element count.

Files changed:
- `cookbook/17_tree_of_thought/tree_of_thought.spl`
- `cookbook/04_model_showdown/showdown_map.spl`

---

## Milestones

- **First public internet momagrid test** — hub exposed via Pinggy
  (`https://qgzqm-99-111-153-200.run.pinggy-free.link`), all 45 recipes
  dispatched and completed successfully over WAN.
- **New recipes added:** 41, 42, 43, 44, 45, 47, 48, 49 (total active: 45)
- **Previous best:** 44/45 (recipe 17 failed due to `len()` bug)
- **Today:** 45/45 — full green

---

## Performance Notes

- Fastest recipe: #45 Vision to Action (3.7s), #27 Data Extraction (6.2s)
- Slowest recipe: #20 Ensemble Voting (367.6s), #16 Reflection Agent (362.6s)
- Recipe 17 Tree of Thought: 348.9s (previously FAILED, now OK with COUNT fix)
- Parallel dispatch with 10 workers kept total wall time to 434.6s despite
  individual recipes taking up to 367s
