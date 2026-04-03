# Recipe 15 — Automated Code Review

**Pattern:** Detect Language → Multi-Pass Analysis (Security, Perf, Style, Bugs) → Synthesis

This recipe demonstrates a comprehensive, multi-pass analysis workflow. In SPL, 
the entire orchestration of multiple LLM "experts" and deterministic file handling 
is expressed in ~80 lines.

---

## The SPL Program

```sql
WORKFLOW code_review
DO
    -- 1. Deterministic file handling
    CALL read_file(@code) INTO @file_content

    -- 2. Language detection (LLM)
    GENERATE language(code) INTO @language
    
    -- 3. Parallel-ready multi-pass analysis (LLM)
    GENERATE security_audit(@code_to_review, @language) INTO @security_findings
    GENERATE performance_review(@code_to_review, @language) INTO @perf_findings
    GENERATE style_review(@code_to_review, @language) INTO @style_findings
    GENERATE bug_detection(@code_to_review, @language) INTO @bug_findings

    -- 4. Synthesis (LLM)
    GENERATE synthesize_review(...) INTO @review
END
```

### Why SPL for Multi-Pass Analysis?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Pipelining** | Native imperative flow | Node-to-node graph | Sequential task lists |
| **Logic** | Native `EVALUATE` for verdict branching | Conditional edges | Manual Python `if/else` |
| **File I/O** | Built-in `read_file`, `write_file` | Manual Python file handling | Manual Python file handling |
| **Brevity** | ~80 lines | ~150 lines | ~130–140 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Excellent for modeling the review process as a clear state-machine; easy to add complex loops if the synthesis requires multi-turn refinement.
- **Cons:** High boilerplate for a process that is essentially a linear sequence of independent analysis steps.

### AutoGen
- **Pros:** Can model a "Review Board" conversation where different agents (Security Expert, Performance Guru) debate the findings.
- **Cons:** For a standard automated report, the conversational overhead and manual state tracking make it more verbose than necessary.

### CrewAI
- **Pros:** Role-based specialization (e.g., "Code Auditor") makes prompt engineering feel natural; handles task context passing elegantly.
- **Cons:** Setup of multiple `Task` objects and the `Crew` orchestrator is verbose for a single-file review.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on efficiency.** Multi-pass analysis is expressed as a simple sequence of `GENERATE` calls. SPL's built-in file handling and deterministic control flow (`EVALUATE`) eliminate the need for significant "glue code."
- **Cons:** Best for structured, expert-led analysis; less focused on free-form collaborative "discussion" between framework agents.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/15_code_review/code_review.spl \
    --adapter ollama -m gemma3 \
    code="def foo(x): return eval(x)"
```

### 2. LangGraph
```bash
python cookbook/15_code_review/langgraph/code_review_langgraph.py \
    --code "def foo(x): return eval(x)"
```

### 3. AutoGen
```bash
python cookbook/15_code_review/autogen/code_review_autogen.py \
    --code "def foo(x): return eval(x)"
```

### 4. CrewAI
```bash
python cookbook/15_code_review/crewai/code_review_crewai.py \
    --code "def foo(x): return eval(x)"
```
