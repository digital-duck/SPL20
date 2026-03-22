# Recipe 08: RAG Query

Retrieval-augmented generation — indexes documents as paragraph chunks, retrieves the most semantically relevant sections, and answers questions from that context.

## Setup

```bash
pip install numpy faiss-cpu sentence-transformers
```

The vector store uses `all-MiniLM-L6-v2` (384-dim, CPU) for semantic embeddings automatically when `sentence-transformers` is installed. Falls back to a character-hash embedding if not installed (poor retrieval quality — not recommended).

### Reset the vector store

```bash
rm -f .spl/vectors.faiss .spl/vectors_meta.db
```

### Index a document by paragraph (one-time setup)

Chunking by paragraph gives precise retrieval — `top_k=3` returns the 3 most *semantically relevant* sections rather than the whole document truncated to fit the token budget.

When given a file path, `spl rag add` reads the file and chunks by paragraph automatically:

```bash
spl rag add /home/gongai/projects/digital-duck/zinets/who-is-wen.md
```

To index as a single document instead:

```bash
spl rag add /home/gongai/projects/digital-duck/zinets/who-is-wen.md --no-chunk
```

Verify:

```bash
spl rag count
spl rag query "Who is Wen?" --top-k 3
```

## Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `question` | TEXT | *(required)* | The question to answer using indexed documents |

## Usage

```bash
spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="Who is Wen?" \
    2>&1 | tee cookbook/out/08_rag_query-$(date +%Y%m%d_%H%M%S).md

spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="What is Momagrid and why was it built?"

spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="What is the Gang of Four in the ZiNets research team?"

spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="What is eta_AI and how is it measured?"

spl run cookbook/08_rag_query/rag_query.spl --adapter ollama \
    question="How did Wen transition from physics to software engineering?"
```

## Notes

- The embedding model is persisted in the store's `config` table — the same model is always used for a given index. Reset the store if you need to switch models.
- `top_k=3` retrieves the 3 most relevant paragraphs by cosine similarity.
- Run `spl rag query "your question"` to inspect retrieved context before running the full prompt.
- GPU acceleration is not required; CPU inference works well for typical document sizes.
