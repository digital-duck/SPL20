# Recipe 21 — Multi-Model Pipeline

**Pattern:** Research → Analysis → Writing → Quality Check → (optional) Loop

This recipe demonstrates the power of per-step model selection and semantic loops. 
In SPL, choosing a specific model for a specific task is a first-class language 
primitive using `USING MODEL`.

---

## The SPL Program

```sql
WORKFLOW multi_model_pipeline
DO
  -- Step 1: Research with a fast model
  GENERATE research(@topic) USING MODEL 'gemma3' INTO @facts

  -- Step 2: Analysis with a reasoning model
  GENERATE analyze(@facts) USING MODEL 'gemma3' INTO @analysis

  -- Step 3: Writing with a creative model
  GENERATE write_summary(@analysis) USING MODEL 'gemma3' INTO @draft

  -- Step 4: Quality loop
  WHILE @iteration < @max_iterations DO
    GENERATE quality_check(@draft) INTO @quality
    EVALUATE @quality
      WHEN > 0.7 THEN RETURN @draft
      ELSE GENERATE write_summary(@analysis) INTO @draft
    END
  END
END
```

### Why SPL for Multi-Model Pipelines?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Model Selection** | First-class `USING MODEL` | Parameterized in node functions | Defined in agent `llm_config` or `llm` |
| **Pipelining** | Native imperative flow | Node-to-node graph | Sequential task lists |
| **Logic** | Native `EVALUATE` | Conditional edges | Manual Python `if/else` |
| **Brevity** | ~60 lines | ~120 lines | ~110–120 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Precise control over model assignment per node; excellent for modeling the quality feedback loop as a state transition.
- **Cons:** High boilerplate; requires defining a new model instance or parameter for each step if they differ.

### AutoGen
- **Pros:** Each agent can be pre-configured with the ideal model for its persona (e.g., the "Researcher" gets a fast model, the "Analyst" gets a reasoning model).
- **Cons:** Standard iterative refinement requires significant "glue code" to manage the loop and extract the final message.

### CrewAI
- **Pros:** Agents are naturally "specialized," making the multi-model concept fit perfectly with the role-based abstraction.
- **Cons:** Lacks native looping; re-instantiating tasks in a Python loop is verbose.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on flexibility.** You can swap models for any single `GENERATE` call with a one-line change. The `WHILE` and `EVALUATE` primitives make the quality-gating logic incredibly clean and readable.
- **Cons:** Model selection is explicit per call; for large fleets of agents, managing individual `USING MODEL` statements might be more manual than pre-configuring agent objects.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/21_multi_model_pipeline/multi_model.spl \
    --adapter ollama --model gemma3 \
    topic="climate change"
```

### 2. LangGraph
```bash
python cookbook/21_multi_model_pipeline/langgraph/multi_model_langgraph.py \
    --topic "climate change"
```

### 3. AutoGen
```bash
python cookbook/21_multi_model_pipeline/autogen/multi_model_autogen.py \
    --topic "climate change"
```

### 4. CrewAI
```bash
python cookbook/21_multi_model_pipeline/crewai/multi_model_crewai.py \
    --topic "climate change"
```
