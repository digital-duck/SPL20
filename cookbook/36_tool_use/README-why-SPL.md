# Recipe 36 — Tool-Use / Function-Call

**Pattern:** Deterministic Python Tools (CALL) → Natural Language Narrative (GENERATE)

This recipe highlights the core architectural principle of SPL: keep deterministic 
logic (math, data fetching) in Python tools and use the LLM only for what it 
does best—language.

---

## The SPL Program

```sql
WORKFLOW sales_analysis
DO
  -- Instant, 0 tokens, 100% reliable
  CALL sum_values(@sales)            INTO @total
  CALL average_values(@sales)        INTO @avg
  CALL percentage_change(@prev, @curr) INTO @growth

  -- Probabilistic narrative
  GENERATE sales_report(@total, @avg, @growth, ...) INTO @report
END
```

### Why SPL for Tool-Use?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Logic Routing** | Native imperative `CALL` | Node-to-node transitions | LLM-based tool "choice" |
| **Reliability** | 100% (tools called by script) | Depends on Graph wiring | < 100% (LLM can hallucinate args) |
| **Performance** | Instant (no tool "reasoning" needed) | Node overhead | High (LLM must plan the tool call) |
| **Brevity** | ~30 lines | ~80 lines | ~70 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Clear separation of concerns between math nodes and generation nodes.
- **Cons:** High boilerplate; defining a simple calculation as a "node" in a state machine adds unnecessary complexity.

### AutoGen
- **Pros:** Agents can "discuss" the results of the tool calls.
- **Cons:** Even for simple math, AutoGen usually expects the agent to "see" the tool and decide to call it, which consumes tokens and introduces a point of failure (hallucinated arguments).

### CrewAI
- **Pros:** High-level abstraction for "Sales Analyst" with a toolbelt.
- **Cons:** Verbose setup; the framework is designed for agentic tool use (reasoning about tools), which is overkill for deterministic data pipelines.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on efficiency and reliability.** SPL treats Python tools as first-class citizens. By using `CALL`, the developer ensures the math is always correct and never uses a single token. It provides the most direct "bridge" between traditional software and LLMs.
- **Cons:** Best for known tool paths; less flexible for "autonomous agents" who must discover tools at runtime.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/36_tool_use/tool_use.spl \
    --adapter ollama --tools cookbook/36_tool_use/tools.py \
    sales="1200,1450,1380,1600,1750,1900"
```

### 2. LangGraph
```bash
python cookbook/36_tool_use/langgraph/tool_use_langgraph.py \
    --sales "1200,1450,1380,1600,1750,1900"
```

### 3. AutoGen
```bash
python cookbook/36_tool_use/autogen/tool_use_autogen.py \
    --sales "1200,1450,1380,1600,1750,1900"
```

### 4. CrewAI
```bash
python cookbook/36_tool_use/crewai/tool_use_crewai.py \
    --sales "1200,1450,1380,1600,1750,1900"
```
