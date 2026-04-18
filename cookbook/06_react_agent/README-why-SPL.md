# Recipe 06 — ReAct Agent (Population Growth)

**Pattern:** Deterministic Tool Call (CALL) → Python Math (CALL) → LLM Narrative (GENERATE)

This recipe demonstrates the "ReAct" (Reason + Act) pattern, specifically highlighting 
the efficiency gains of SPL's `CALL` vs. probabilistic framework loops.

---

## The SPL Program

```sql
WORKFLOW population_growth
  INPUT: @country TEXT, @year_curr INTEGER
DO
  -- Step 1: Deterministic Fetch (0 LLM tokens)
  CALL search_population(@country, @year_prev) INTO @pop_prev
  CALL search_population(@country, @year_curr) INTO @pop_curr

  -- Step 2: Deterministic Math (0 LLM tokens)
  CALL calc_growth_rate(@pop_prev, @pop_curr) INTO @growth_rate

  -- Step 3: Probabilistic Narrative (LLM used only here)
  GENERATE growth_report(@country, @year_prev, @pop_prev, @year_curr, @pop_curr, @growth_rate) 
    INTO @report
END
```

### Why SPL for Tool-Heavy Workflows?

| Feature | SPL | LangGraph / AutoGen / CrewAI |
|---|---|---|---|
| **Tool Execution** | Deterministic `CALL` (0 tokens) | Probabilistic (LLM must "choose" the tool) |
| **Logic Flow** | Native script execution | State machine or agent conversation |
| **Reliability** | 100% (tools are routed by code) | < 100% (LLM might hallucinate tool arguments) |
| **Brevity** | ~50 lines | ~80–120 lines |
| **Cost** | Minimal (1 LLM call) | Variable (Multiple LLM turns to "think" and "act") |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Excellent for complex cycles and stateful error recovery.
- **Cons:** High boilerplate; no native distinction between deterministic Python nodes and LLM nodes.

### AutoGen
- **Pros:** Natural for multi-agent validation (e.g., a "Coder" agent calling the tool).
- **Cons:** Orchestration of a simple linear tool sequence feels heavy; requires manual chat history parsing to extract results.

### CrewAI
- **Pros:** Very high-level; agents are "self-aware" of their tools.
- **Cons:** Probabilistic by nature; even a simple math calculation often requires the agent to "plan" and "reason," which consumes tokens and adds latency.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/06_react_agent/react_agent.spl \
    --adapter ollama --model gemma3 --tools cookbook/06_react_agent/tools.py \
    country="France"
```

### 2. LangGraph
```bash
python cookbook/06_react_agent/langgraph/react_langgraph.py --country France
```

### 3. AutoGen
```bash
python cookbook/06_react_agent/autogen/react_autogen.py --country France
```

### 4. CrewAI
```bash
python cookbook/06_react_agent/crewai/react_crewai.py --country France
```
