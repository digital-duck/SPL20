---
name: SPL Language Vision and Origin Story
description: Core design philosophy of SPL v2.0 — the PL/SQL lineage, symphony metaphor, and Wen+Claude collaboration story
type: project
---

SPL v2.0 is the GenAI-era equivalent of PL/SQL: just as Oracle's PL/SQL extended SQL (declarative data) with procedural power (Python-like control flow), SPL extends declarative LLM invocation with the best of three languages:

- **SQL** — declare *what* to invoke (PROMPT, SELECT, GENERATE, COMMIT)
- **Python** — control *how* it flows (WHILE, EVALUATE, EXCEPTION, types, f-strings)
- **Bash** — *compose* and pipe results (| operator, redirection-style LOGGING, @var substitution)

**Origin:** Wen's spark came from PL/SQL on a Tuesday (2026-03-18 approx). The retrospective insight: SPL v2.0 should inject the best of Python and Bash into SQL's declarative bones — one beautiful language for GenAI application development.

**The symphony metaphor:** SPL is a score format for the new AI orchestra. Developers write their scores; the AI (LLMs, tools, adapters) plays them. SPL doesn't require the composer to understand how the instruments work internally.

**The collaboration story:** Built by Wen + Claude (The AI Quartet context). Wen brings 7-year cloud data engineering intuition — where PL/SQL fell short, which bash idioms survive, why Python glue becomes maintenance burden. Claude brings cross-language pattern recognition. Neither produces this alone. The artifact embodies the method: a language for human-AI collaboration, itself built through human-AI collaboration.

**Design principle — grammar orthogonality:** Minimum orthogonal constructs. Don't add IF/FOR/CASE if EVALUATE/WHILE already covers the ground. Every new keyword must add expressive power not achievable by existing ones. Avoid Python-envy.

**Design principle — contextual grammar (Chinese linguistic insight):** A keyword can be both noun and verb by context (like Chinese 记录). EXCEPTION, LOGGING — both name a concept AND perform an action. Fewer reserved words, richer meaning per token.

**Why:** SPL should make a Python dev, SQL analyst, and DevOps engineer all read the same workflow fluently. Zero context-switching. That's the target.
