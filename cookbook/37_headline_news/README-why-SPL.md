# Recipe 37 — Headline News Aggregator

**Pattern:** Generate → Expand → Evaluate → (optional) Fill Gaps → Format

This recipe demonstrates a multi-stage synthesis pipeline with a quality-gated 
refinement step. In SPL, this complex sequence of generating, expanding, 
and evaluating news is expressed as a clear, top-to-bottom script.

---

## The SPL Program

```sql
WORKFLOW headline_news
DO
    -- 1. Generate core headlines
    GENERATE generate_headlines(...) INTO @headlines

    -- 2. Expand into summaries
    GENERATE expand_headlines(@headlines, ...) INTO @expanded

    -- 3. Evaluate coverage quality
    GENERATE evaluate_coverage(@expanded, ...) INTO @coverage_score

    -- 4. Conditional refinement
    EVALUATE @coverage_score
        WHEN > 0.75 THEN
            GENERATE format_digest(@expanded, ...) INTO @digest
        ELSE
            GENERATE fill_coverage_gaps(@expanded, ...) INTO @expanded
            GENERATE format_digest(@expanded, ...) INTO @digest
    END
END
```

### Why SPL for News Aggregation?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Pipelining** | Native imperative flow | Node-to-node graph | Sequential task lists |
| **Logic** | Native `EVALUATE` for gaps | Conditional edges | Python `if/else` |
| **State** | Simple `@variables` | `TypedDict` updates | Manual Python state management |
| **Brevity** | ~90 lines | ~160 lines | ~140 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Excellent visualization of the multi-stage pipeline; state machine logic makes the "fill gaps" cycle very clear.
- **Cons:** High boilerplate; every small formatting or expansion step requires a dedicated node function and state wiring.

### AutoGen
- **Pros:** Modeling the process as a conversation between an "Editor" and an "Analyst" is intuitive and mimics a real newsroom.
- **Cons:** Standard sequential data processing (passing the list of headlines through multiple transforms) requires significant "manual" Python orchestration.

### CrewAI
- **Pros:** High-level abstractions for "Editor" and "Analyst" roles make the prompt engineering feel very natural.
- **Cons:** No native looping/conditional logic; re-running tasks based on a coverage score requires complex manual control flow in Python.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on logic density.** SPL allows you to define complex prompts as reusable `FUNCTION`s and then orchestrate them in a clean, imperative `WORKFLOW`. It captures the "business logic" of the newsroom without the infrastructure overhead.
- **Cons:** Best for well-defined synthesis tasks; less focused on creative multi-agent "brainstorming" than AutoGen.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/37_headline_news/headline_news.spl \
    --adapter ollama --model gemma3 \
    topic="artificial intelligence"
```

### 2. LangGraph
```bash
python cookbook/37_headline_news/langgraph/headline_news_langgraph.py \
    --topic "artificial intelligence"
```

### 3. AutoGen
```bash
python cookbook/37_headline_news/autogen/headline_news_autogen.py \
    --topic "artificial intelligence"
```

### 4. CrewAI
```bash
python cookbook/37_headline_news/crewai/headline_news_crewai.py \
    --topic "artificial intelligence"
```
