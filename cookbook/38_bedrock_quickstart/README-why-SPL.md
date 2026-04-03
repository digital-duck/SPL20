# Recipe 38 — Bedrock Quickstart

**Pattern:** Fan-out (Parallel prompt execution) → Synthesis / Comparison

This recipe demonstrates parallel model execution and cross-model comparison. 
In SPL, the `WITH` clause (Common Table Expressions) provides a natural way to 
express parallel LLM calls, which are then synthesized in a single `SELECT` 
and `GENERATE` step.

---

## The SPL Program

```sql
WORKFLOW bedrock_quickstart
DO
    -- Parallel fan-out
    WITH
        r1 AS (GENERATE answer(@prompt) USING MODEL @m1),
        r2 AS (GENERATE answer(@prompt) USING MODEL @m2),
        r3 AS (GENERATE answer(@prompt) USING MODEL @m3)
    SELECT r1.answer, r2.answer, r3.answer INTO @a1, @a2, @a3

    -- Comparative synthesis
    GENERATE compare_models(@prompt, @m1, @a1, @m2, @a2, @m3, @a3) INTO @comparison
END
```

### Why SPL for Multi-Model Comparison?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Parallelism** | Native `WITH` (parallel by default) | Node branches or manual `asyncio` | Manual sequential or custom parallel loop |
| **Model Selection** | Explicit per-step `USING MODEL` | Parameterized in node functions | Defined in agent config |
| **Data Joining** | Direct `SELECT ... INTO` | State merging logic | Manual variable tracking |
| **Brevity** | ~50 lines | ~100 lines | ~90 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Robust error handling for individual model failures; clear graph visualization of the fan-out pattern.
- **Cons:** High boilerplate for state definition and node wiring; managing parallel execution requires understanding LangGraph's branching logic.

### AutoGen
- **Pros:** Can model each model as a different agent and have them "debate" their own answers.
- **Cons:** Standard fan-out (identical prompt to N models) is not the primary use case; requires manual orchestration of multiple `initiate_chat` calls.

### CrewAI
- **Pros:** Elegant role-based abstraction where each model is assigned a specific "Expert" role.
- **Cons:** Executing the same prompt across different models requires creating separate Agent/Task objects for each, leading to verbose code for a simple comparison.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on parallel expressiveness.** The `WITH` block is the most elegant way to express "run these N things and give me the results at once." It mimics SQL's declarative nature, making the intention of the workflow immediately clear.
- **Cons:** Best for static fan-out; more complex dynamic fan-out (N determined at runtime) requires standard imperative `WHILE` loops.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/38_bedrock_quickstart/bedrock_quickstart.spl \
    --adapter bedrock \
    prompt="Explain the CAP theorem in two sentences."
```

### 2. LangGraph
```bash
python cookbook/38_bedrock_quickstart/langgraph/bedrock_langgraph.py \
    --prompt "Explain the CAP theorem in two sentences."
```

### 3. AutoGen
```bash
python cookbook/38_bedrock_quickstart/autogen/bedrock_autogen.py \
    --prompt "Explain the CAP theorem in two sentences."
```

### 4. CrewAI
```bash
python cookbook/38_bedrock_quickstart/crewai/bedrock_crewai.py \
    --prompt "Explain the CAP theorem in two sentences."
```
