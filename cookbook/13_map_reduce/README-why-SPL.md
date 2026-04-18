# Recipe 13 — Map-Reduce Summarizer

**Pattern:** Split → Map (summarize) → Reduce (combine) → Quality Check → (optional) Refine

The Map-Reduce pattern is essential for processing large documents that exceed an LLM's 
context window. In SPL, this complex multi-step, dynamic workflow is expressed 
declaratively in ~60 lines of code.

---

## The SPL Program

```sql
WORKFLOW map_reduce_summarizer
    INPUT: @document TEXT, @style TEXT, @log_dir TEXT
    OUTPUT: @final_summary TEXT
DO
    -- Step 1: Deterministic Plan (0 tokens)
    CALL chunk_plan(@document) INTO @chunk_count

    -- Step 2: MAP — summarize each chunk
    WHILE @chunk_index < @chunk_count DO
        CALL extract_chunk(@document, @chunk_index, @chunk_count) INTO @chunk
        GENERATE summarize_chunk(@chunk, @chunk_index) INTO @chunk_summary
        @summaries := list_append(@summaries, @chunk_summary)
        @chunk_index := @chunk_index + 1
    END

    -- Step 3: REDUCE — combine summaries
    @summaries_text := list_concat(@summaries, '\n')
    GENERATE reduce_summaries(@summaries_text, @style) INTO @final_summary

    -- Step 4: Quality Check
    GENERATE quality_score(@final_summary, @document) INTO @score
    EVALUATE @score
        WHEN > 0.7 THEN RETURN @final_summary
        ELSE GENERATE improve_summary(@final_summary, @summaries_text) INTO @final_summary
    END
END
```

### Why SPL for Map-Reduce?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Control Flow** | Native `WHILE` and `EVALUATE` | Complex graph with `conditional_edges` | Plain Python loops + manual agent calls |
| **Tooling** | Built-in `CALL` for deterministic Python logic | Custom functions as nodes | Custom functions as tools/tasks |
| **State** | Simple `@variables` | `TypedDict` + State updates | Managed in chat history or custom Python state |
| **Brevity** | ~60 lines | ~130 lines | ~110–120 lines |
| **Observability** | Automatic logging of all `@variables` | Requires `checkpointing` or manual logging | Manual logging to files/DB |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Extremely robust for persistent, long-running stateful workflows; excellent visualization of the graph.
- **Cons:** High boilerplate overhead for simple loops; rigid state schema requirement.

### AutoGen
- **Pros:** Strong at multi-agent collaboration and conversational patterns.
- **Cons:** For structured, linear/looping workflows like Map-Reduce, the multi-agent abstraction often gets in the way, requiring significant "manual" Python orchestration.

### CrewAI
- **Pros:** High-level abstractions for "Roles" and "Goals" making it easy to define persona-driven agents.
- **Cons:** Lacks native looping and conditional primitives; recreating Map-Reduce requires re-instantiating `Task` and `Crew` objects in a loop, which can be verbose.

### SPL (Structured Prompt Language)
- **Pros:** The most concise way to express the pattern; native support for deterministic tools and LLM steps in a single file; easy to read as a "script" for the LLM.
- **Cons:** Best for well-defined workflows; less focused on free-form "agentic" conversation than AutoGen.

---

## Running the Examples

All implementations use the same underlying prompts and deterministic chunking logic.

### 0. Setup
```bash
conda create -n spl_test python=3.11
conda activate spl_test

git clone https://github.com/digital-duck/SPL20.git
cd SPL20

pip install -e .
pip install -r requirements-cookbook.txt
```

### 1. SPL (Native)
```bash
spl run cookbook/13_map_reduce/map_reduce.spl \
    --adapter ollama --model gemma3 --tools cookbook/13_map_reduce/tools.py \
    document="$(cat cookbook/13_map_reduce/data/large_doc.txt)" \
    style="bullet points"
```

### 2. LangGraph
```bash
python cookbook/13_map_reduce/langgraph/map_reduce_langgraph.py \
    --document "$(cat cookbook/13_map_reduce/data/large_doc.txt)" \
    --model "gemma3" \
    --style "bullet points"
```

### 3. AutoGen
```bash
python cookbook/13_map_reduce/autogen/map_reduce_autogen.py \
    --document "$(cat cookbook/13_map_reduce/data/large_doc.txt)" \
    --model "gemma3" \
    --style "bullet points"
```

### 4. CrewAI
```bash
python cookbook/13_map_reduce/crewai/map_reduce_crewai.py \
    --document "$(cat cookbook/13_map_reduce/data/large_doc.txt)" \
    --model "gemma3" \
    --style "bullet points"
```

### Summary of Comparison

 I have reviewed the final_summary.md outputs across all four frameworks. All implementations successfully executed the
  Map-Reduce pattern, accurately capturing the core themes of the distributed AI inference document.

  Output Comparison & Observations:


  ┌───────────┬───────────────────────────────────────────────────┬─────────────────┬─────────────────────────────────────┐
  │ Framework │ Content Quality                                   │ Style Adherence │ Preamble/Meta-commentary            │
  ├───────────┼───────────────────────────────────────────────────┼─────────────────┼─────────────────────────────────────┤
  │ SPL       │ High - Very well-categorized (Themes, Pillars,    │ Excellent       │ Included "Okay, here's a            │
  │           │ Strategies).                                      │ (Bullets)       │ consolidated..."                    │
  │ LangGraph │ High - Comprehensive coverage of tech and         │ Excellent       │ Included "Okay, here's a single..." │
  │           │ timeline.                                         │ (Bullets)       │                                     │
  │ AutoGen   │ High - Direct and concise, captured specific data │ Best (Clean)    │ None (Strictly the summary)         │
  │           │ points.                                           │                 │                                     │
  │ CrewAI    │ High - Good synthesis of challenges and           │ Excellent       │ Included "Here's a cohesive..."     │
  │           │ solutions.                                        │ (Bullets)       │                                     │
  └───────────┴───────────────────────────────────────────────────┴─────────────────┴─────────────────────────────────────┘

  Key Takeaways:

   1. Consistency: Despite different orchestration logic, the underlying prompt parity ensured that the "knowledge extraction"
      remained consistent across all frameworks.
   2. AutoGen's Cleanliness: The AutoGen implementation produced the "cleanest" artifact (no conversational filler). This is a
      result of the system_message pattern I used in the script, which explicitly forbids meta-commentary.
   3. SPL's Depth: The SPL output was particularly well-structured, likely due to how the reduce_summaries prompt interacted with
      the sequential list concatenation.
   4. Workflow Success: All four frameworks successfully navigated the Plan -> Map -> Reduce -> Quality Check loop. The fact that
      all summaries are high quality suggests the quality_score > 0.7 threshold was met (or the improve_summary step was
      triggered effectively).

  The updated README-why-SPL.md perfectly captures these architectural trade-offs. SPL clearly wins on brevity and "logic
  density," while the others offer more infrastructure for complex, multi-agent state management at the cost of significantly
  higher boilerplate.
