# Recipe 14 — Multi-Agent Collaboration

**Pattern:** Researcher → Analyst → Writer (Sequential Delegation)

This recipe demonstrates multi-agent collaboration. In SPL, specialized agents are 
implemented as simple `PROCEDURE` blocks, and the orchestrator is a `WORKFLOW` that 
coordinates them with standard `CALL` statements.

---

## The SPL Program

```sql
PROCEDURE researcher(topic TEXT) RETURN TEXT DO ... END
PROCEDURE analyst(research TEXT, topic TEXT) RETURN TEXT DO ... END
PROCEDURE writer(research TEXT, analysis TEXT, topic TEXT) RETURN TEXT DO ... END

WORKFLOW multi_agent_report
DO
    CALL researcher(@topic) INTO @research
    CALL analyst(@research, @topic) INTO @analysis
    CALL writer(@research, @analysis, @topic) INTO @report
END
```

### Why SPL for Multi-Agent?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Delegation** | Native `CALL` (like functions) | Node-to-node graph transitions | Agent-to-agent chat or task lists |
| **Separation** | Procedures provide clean encapsulation | Nodes are plain Python functions | Agents are persona-based objects |
| **Orchestration** | Standard imperative script | Graph wiring | Process orchestration (sequential/hierarchical) |
| **Brevity** | ~60 lines | ~100 lines | ~100 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Precise control over the flow and state at each step.
- **Cons:** Boilerplate for simple sequential handoffs.

### AutoGen
- **Pros:** Excellent for modeling conversations between agents.
- **Cons:** Standard sequential task handoff requires repetitive `initiate_chat` or `GroupChat` setup.

### CrewAI
- **Pros:** Strong "Role" and "Goal" abstractions; handles context passing automatically between tasks.
- **Cons:** Re-instantiating the entire `Crew` or `Task` list for simple scripts can feel heavy.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on simplicity.** Multi-agent collaboration is modeled after standard software procedures. One agent (procedure) simply calls another, passing data through `@variables`.
- **Cons:** Best for structured, deterministic handoffs; less focused on free-form agentic "debates" than AutoGen.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/14_multi_agent/multi_agent.spl \
    --adapter ollama --model gemma3 \
    topic="Impact of AI on healthcare"
```

### 2. LangGraph
```bash
python cookbook/14_multi_agent/langgraph/multi_agent_langgraph.py \
    --topic "Impact of AI on healthcare"
```

### 3. AutoGen
```bash
python cookbook/14_multi_agent/autogen/multi_agent_autogen.py \
    --topic "Impact of AI on healthcare"
```

### 4. CrewAI
```bash
python cookbook/14_multi_agent/crewai/multi_agent_crewai.py \
    --topic "Impact of AI on healthcare"
```
