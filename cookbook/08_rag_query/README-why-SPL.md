# Recipe 08 — RAG Query

**Pattern:** Document Indexing → Semantic Retrieval (RAG) → LLM Generation

This recipe demonstrates Retrieval-Augmented Generation (RAG). In SPL, the entire 
retrieval and generation pipeline is condensed into a single `PROMPT` block using 
the built-in `rag.query` tool.

---

## The SPL Program

```sql
PROMPT rag_answer
SELECT
    system_role('You are a knowledgeable assistant. Use the provided context to answer accurately.'),
    rag.query(context.question, top_k=3) AS background,
    context.question AS question
GENERATE answer(question)
```

### Why SPL for RAG?

| Feature | SPL | LangGraph / AutoGen / CrewAI |
|---|---|---|---|
| **Retrieval** | Built-in `rag.query` (0 tokens) | Manual setup of VectorDB, Embeddings, and Search |
| **Complexity** | Extremely Low (1 `PROMPT` block) | High (Manual indexing, splitting, and querying) |
| **Brevity** | ~10 lines | ~100–120 lines |
| **Configuration** | Handled by `spl doc-rag` CLI | Explicitly coded in Python |

---

## Framework Comparison Highlights

### LangGraph
- **Pros:** Precise control over the indexing and retrieval nodes.
- **Cons:** High boilerplate (requires defining State, Nodes, and Graph wiring for what is essentially a linear call).

### AutoGen
- **Pros:** Can easily extend to "multi-agent RAG" where one agent retrieves and another fact-checks.
- **Cons:** Standard RAG requires significant "glue code" to manage document loading and vector store interaction.

### CrewAI
- **Pros:** Agents can be given "Knowledge" tools natively.
- **Cons:** Setup is verbose; requires creating `Agent`, `Task`, and `Crew` objects even for a simple query-answer flow.

### SPL (Structured Prompt Language)
- **Pros:** **Winner on brevity.** RAG is treated as a first-class primitive. The `rag.query` call is seamlessly integrated into the `SELECT` block, making context injection automatic.
- **Cons:** Native `rag.query` uses the default system vector store; custom RAG logic requires using `CALL` to external Python tools.

---

## Running the Examples

### 1. SPL (Native)
```bash
# First, index a document
spl doc-rag add path/to/your/document.md

# Then run the query
spl run cookbook/08_rag_query/rag_query.spl \
    --adapter ollama --model gemma3 \
    question="What is Momagrid?"
```

### 2. LangGraph
```bash
python cookbook/08_rag_query/langgraph/rag_langgraph.py \
    --doc path/to/your/document.md \
    --question "What is Momagrid?"
```

### 3. AutoGen
```bash
python cookbook/08_rag_query/autogen/rag_autogen.py \
    --doc path/to/your/document.md \
    --question "What is Momagrid?"
```

### 4. CrewAI
```bash
python cookbook/08_rag_query/crewai/rag_crewai.py \
    --doc path/to/your/document.md \
    --question "What is Momagrid?"
```
