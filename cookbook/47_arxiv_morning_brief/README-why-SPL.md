# Recipe 47 — arXiv Morning Brief

**Pattern:** PDF Download → Chunking → Per-Chunk Summary → Per-Paper Abstract → Assemble Brief

This recipe demonstrates a complex, hierarchical Map-Reduce pattern. In SPL, the 
entire flow from downloading PDFs to nested chunk-summarization and final 
brief assembly is expressed in ~100 lines.

---

## The SPL Program

```sql
WORKFLOW arxiv_morning_brief
DO
    -- 1. Outer loop over papers
    WHILE @i < @n DO
        -- Step A: download PDF
        CALL download_arxiv_pdf(@url) INTO @pdf_path

        -- Step B: chunking
        CALL semantic_chunk_plan(@pdf_path) INTO @chunks

        -- Step C: Inner loop over chunks (Map)
        WHILE @j < @m DO
            GENERATE chunk_summarizer(@chunk, ...) INTO @chunk_summary
        END

        -- Step D: Paper reduction (Reduce)
        GENERATE paper_reducer(@summaries) INTO @paper_summary
    END

    -- 2. Final assembly
    GENERATE brief_writer(@header, @paper_summaries, ...) INTO @brief
END
```

### Why SPL for Complex Pipelining?

| Feature | SPL | LangGraph | AutoGen / CrewAI |
|---|---|---|---|
| **Hierarchy** | Native nested `WHILE` loops | Sub-graphs or manual loops in nodes | Manual Python loops over agent tasks |
| **Tool Integration** | Native `CALL` for PDFs/Chunking | Custom nodes for Python tools | Custom tools/tasks |
| **Logic** | Clean imperative script | Complex graph wiring | Distributed Python orchestration |
| **Brevity** | ~100 lines | ~180 lines | ~150 lines |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Sub-graphs allow for precise modeling of the paper-processing lifecycle; extremely robust state management for long-running batch jobs.
- **Cons:** High boilerplate; nesting loops (papers -> chunks) in a graph requires either complex `conditional_edges` or "fat" nodes that hide the internal loop.

### AutoGen
- **Pros:** "Summarizer" and "Editor" agents can have distinct technical vs. editorial personas.
- **Cons:** Orchestrating a rigid data pipeline (PDF -> Chunks -> Summary) through conversational interfaces adds significant latency and parsing logic.

### CrewAI
- **Pros:** Tasks can be organized sequentially per paper; context passing makes assembly simple.
- **Cons:** Re-instantiating the `Crew` for every chunk or paper inside a Python loop is verbose and circumvents the framework's primary orchestration model.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on architectural clarity.** SPL excels at hierarchical workflows. The nested `WHILE` loops and direct `CALL`s to PDF processing tools make the "Map-Reduce-Map-Reduce" nature of the task obvious and easy to maintain.
- **Cons:** Best for structured batch processing; less suitable for collaborative, multi-agent "brainstorming" sessions.

---

## Running the Examples

### 1. SPL (Native)
```bash
spl run cookbook/47_arxiv_morning_brief/arxiv_morning_brief.spl \
    --adapter ollama -m gemma3 --tools cookbook/47_arxiv_morning_brief/tools.py \
    urls="https://arxiv.org/pdf/2501.12948"
```

### 2. LangGraph
```bash
python cookbook/47_arxiv_morning_brief/langgraph/arxiv_langgraph.py \
    --urls "https://arxiv.org/pdf/2501.12948"
```

### 3. AutoGen
```bash
python cookbook/47_arxiv_morning_brief/autogen/arxiv_autogen.py \
    --urls "https://arxiv.org/pdf/2501.12948"
```

### 4. CrewAI
```bash
python cookbook/47_arxiv_morning_brief/crewai/arxiv_crewai.py \
    --urls "https://arxiv.org/pdf/2501.12948"
```
