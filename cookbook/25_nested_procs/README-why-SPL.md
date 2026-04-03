# Recipe 25 — Nested Procedures

**Pattern:** Outer Workflow → CALL Inner Procedure → CALL Inner Procedure

This recipe demonstrates procedural nesting and composability. In SPL, 
`PROCEDURE` blocks act as reusable, encapsulated units of logic that can be 
called just like standard functions, including parameter passing and return values.

---

## The SPL Program

```sql
PROCEDURE explain_layer(content TEXT, audience TEXT) RETURN TEXT DO ... END
PROCEDURE make_example(concept TEXT, context TEXT) RETURN TEXT DO ... END

WORKFLOW layered_explainer
DO
    -- Encapsulated sub-tasks called as procedures
    CALL explain_layer(content = @overview, audience = @audience) INTO @base_explanation
    CALL make_example(concept = @topic, context = @base_explanation) INTO @example
END
```

### Why SPL for Nested Procedures?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Composability** | Native `PROCEDURE` (reusable units) | Sub-graphs or function calls | Conversational handoffs or Task context |
| **Interface** | Strongly typed parameters/returns | State schema (`TypedDict`) | Natural language context |
| **Logic** | Native `EVALUATE` within procedures | Conditional edges | Python `if/else` |
| **Brevity** | ~60 lines | ~120 lines | ~100–110 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Sub-graphs allow for extremely deep and complex nesting with isolated state.
- **Cons:** High overhead; every "procedure" requires its own State, Nodes, and Graph definition if modeled as a true sub-graph.

### AutoGen
- **Pros:** Encourages "Delegation" where one agent can initiate a chat with another agent to "solve a sub-problem."
- **Cons:** Managing data return from a sub-chat back to the main orchestration loop requires manual parsing.

### CrewAI
- **Pros:** The `context` parameter in `Task` allows for elegant data passing between sequential steps.
- **Cons:** No native "Procedure" abstraction; logic is distributed across `Task` descriptions rather than encapsulated code blocks.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on composability.** SPL `PROCEDURE`s mirror standard programming functions. They provide the perfect balance of encapsulation (isolated prompts/logic) and ease of use (simple `CALL` syntax).
- **Cons:** Procedures are static; for highly dynamic, runtime-defined agent swarms, a more object-oriented framework might be preferred.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/25_nested_procs/nested_procs.spl \
    --adapter ollama -m gemma3 \
    topic="quantum computing" audience="high school students"
```

### 2. LangGraph
```bash
python cookbook/25_nested_procs/langgraph/nested_procs_langgraph.py \
    --topic "quantum computing" --audience "high school students"
```

### 3. AutoGen
```bash
python cookbook/25_nested_procs/autogen/nested_procs_autogen.py \
    --topic "quantum computing" --audience "high school students"
```

### 4. CrewAI
```bash
python cookbook/25_nested_procs/crewai/nested_procs_crewai.py \
    --topic "quantum computing" --audience "high school students"
```
