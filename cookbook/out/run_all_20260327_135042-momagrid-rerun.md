=== SPL 2.0 Cookbook Batch Run — 2026-03-27 13:50:43 ===
    Overrides : adapter=momagrid
    Mode      : parallel (momagrid — recipes submitted concurrently)

Submitting 4 recipe(s) with 4 parallel worker(s)...

[11] Debate Arena  →  started
[14] Multi-Agent Collaboration  →  started
[15] Code Review  →  started
[23] Structured Output  →  started
[14] Multi-Agent Collaboration  →  FAILED  (0.3s)  log: multi_agent_20260327_135043.md
[23] Structured Output  →  FAILED  (0.3s)  log: structured_output_20260327_135043.md
[11] Debate Arena  →  FAILED  (0.3s)  log: debate_20260327_135043.md
[15] Code Review  →  FAILED  (0.3s)  log: code_review_20260327_135043.md

=== Summary: 0/4 Success  (total 0.3s) ===

ID    Recipe                        Status     Elapsed
--------------------------------------------------------
11    Debate Arena                  FAILED        0.3s
14    Multi-Agent Collaboration     FAILED        0.3s
15    Code Review                   FAILED        0.3s
23    Structured Output             FAILED        0.3s

