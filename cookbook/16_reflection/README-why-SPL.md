# Recipe 16 — Reflection Agent

**Pattern:** Solve → Reflect → Score → (optional) Correct → Loop

The reflection pattern is a meta-cognitive loop where the agent assesses its own 
work before committing. In SPL, this iterative, state-dependent workflow is 
implemented with a simple `WHILE` loop and `EVALUATE` block.

---

## The SPL Program

```sql
WORKFLOW reflection_agent
DO
    -- 1. Initial attempt
    GENERATE solve(@problem) INTO @answer

    -- 2. Reflection loop
    WHILE @iteration < @max_reflections DO
        GENERATE reflect(@problem, @answer) INTO @reflection
        GENERATE confidence_score(@answer, @reflection) INTO @confidence

        EVALUATE @confidence
            WHEN > 0.85 THEN
                RETURN @answer WITH status = 'confident'
            ELSE
                GENERATE correct(@answer, @reflection) INTO @answer
                @iteration := @iteration + 1
        END
    END
END
```

### Why SPL for Reflection?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Loop Control** | Native `WHILE` | Graph cycles + `conditional_edges` | Python `while/for` + manual orchestration |
| **State** | Simple `@variables` | `TypedDict` updates | Manual Python state management |
| **Logic** | Native `EVALUATE` | Conditional edge logic | Python `if/else` |
| **Brevity** | ~60 lines | ~120 lines | ~100–120 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Graph cycles are a first-class citizen; provides excellent tracing of how the solution evolves.
- **Cons:** Boilerplate for defining the graph wiring and the `TypedDict` state.

### AutoGen
- **Pros:** Can model the reflection as a conversation between two distinct agents (the "Solver" and the "Critic").
- **Cons:** For simple self-reflection, the overhead of creating agents and parsing their dialogue can be verbose.

### CrewAI
- **Pros:** Persona-based approach makes the "Reflector" role feel very distinct and effective.
- **Cons:** No native looping construct; requires wrapping CrewAI tasks in a Python loop, leading to verbose task re-definitions.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on readability.** Reflection is expressed as a simple iterative script. The `WHILE` loop and `EVALUATE` block are native language features, making the self-assessment logic feel like standard programming.
- **Cons:** Best for structured loops; less suitable for open-ended "multi-agent brainstorming" than AutoGen.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/16_reflection/reflection.spl \
    --adapter ollama -m gemma3 \
    problem="What are the trade-offs of microservices vs monoliths?"
```

### 2. LangGraph
```bash
python cookbook/16_reflection/langgraph/reflection_langgraph.py \
    --problem "What are the trade-offs of microservices vs monoliths?"
```

### 3. AutoGen
```bash
python cookbook/16_reflection/autogen/reflection_autogen.py \
    --problem "What are the trade-offs of microservices vs monoliths?"
```

### 4. CrewAI
```bash
python cookbook/16_reflection/crewai/reflection_crewai.py \
    --problem "What are the trade-offs of microservices vs monoliths?"
```
