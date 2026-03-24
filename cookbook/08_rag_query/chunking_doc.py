"""chunking_doc.py — Educational script: paragraph chunking for RAG indexing.

Demonstrates why chunking matters for retrieval quality and how the SPL vector
store uses sentence-transformers embeddings to enable semantic search.

Usage:
    python3 -W ignore chunking_doc.py /path/to/document.md [--query "your question"]

Or via the improved CLI (does the same thing in one command):
    spl doc-rag add /path/to/document.md
"""

import argparse
import re
import sys
import time


# ── Step 1: Load the document ─────────────────────────────────────────────────

def load_document(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    print(f"[1] Loaded: {path}")
    print(f"    Size: {len(content):,} chars / ~{len(content.split()):,} words")
    return content


# ── Step 2: Chunk by paragraph ────────────────────────────────────────────────

def chunk_by_paragraph(text: str) -> list[str]:
    """Split on two or more consecutive newlines (blank lines between paragraphs).

    Why paragraph chunking?
    - A single large document as one embedding loses local context.
    - top_k=3 on paragraphs returns the 3 most *relevant* sections.
    - top_k=3 on the whole file just returns the same document 3 times.
    """
    chunks = [c.strip() for c in re.split(r"\n{2,}", text) if c.strip()]
    print(f"\n[2] Chunked into {len(chunks)} paragraphs")
    print(f"    Avg chunk size: {sum(len(c) for c in chunks) // len(chunks):,} chars")
    print(f"    Shortest: {min(len(c) for c in chunks):,} chars")
    print(f"    Longest:  {max(len(c) for c in chunks):,} chars")
    return chunks


# ── Step 3: Index with semantic embeddings ────────────────────────────────────

def index_chunks(chunks: list[str], storage_dir: str = ".spl") -> object:
    """Embed each chunk with all-MiniLM-L6-v2 and store in FAISS + SQLite.

    Why sentence-transformers over character-hash embeddings?
    - Character-hash: deterministic, no deps, zero semantic understanding.
      "Who is Wen?" and "Wen's biography" would score poorly despite being related.
    - all-MiniLM-L6-v2: 384-dim semantic vectors trained on 1B sentence pairs.
      Synonyms, paraphrases, and related concepts score high automatically.
    """
    from spl.storage import get_vector_store

    print(f"\n[3] Indexing {len(chunks)} chunks ...")
    store = get_vector_store("faiss", storage_dir)
    print(f"    Embedding model: {store.model_name}")

    t0 = time.perf_counter()
    ids = store.add_batch(chunks)
    elapsed = time.perf_counter() - t0

    print(f"    Indexed {len(ids)} chunks in {elapsed:.1f}s "
          f"({elapsed / len(ids) * 1000:.1f}ms per chunk)")
    print(f"    Total documents in store: {store.count()}")
    return store


# ── Step 4: Demo retrieval ────────────────────────────────────────────────────

def demo_query(store, query: str, top_k: int = 3) -> None:
    """Show what the LLM will receive as context for a given question.

    This is exactly what rag.query(context.question, top_k=3) does inside SPL.
    """
    print(f"\n[4] Semantic search: {query!r}")
    results = store.query(query, top_k=top_k)
    if not results:
        print("    No results found.")
        return
    for i, r in enumerate(results, 1):
        snippet = r["text"].replace("\n", " ")[:120]
        print(f"    {i}. [score={r['score']:.4f}] {snippet}...")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("document", help="Path to the markdown/text file to index")
    parser.add_argument("--query", default="Who is Wen?",
                        help="Demo query to run after indexing (default: 'Who is Wen?')")
    parser.add_argument("--storage-dir", default=".spl",
                        help="Vector store directory (default: .spl)")
    parser.add_argument("--top-k", type=int, default=3,
                        help="Number of results to retrieve (default: 3)")
    parser.add_argument("--reset", action="store_true",
                        help="Delete existing index before indexing")
    args = parser.parse_args()

    if args.reset:
        import os
        for f in ["vectors.faiss", "vectors_meta.db"]:
            path = os.path.join(args.storage_dir, f)
            if os.path.exists(path):
                os.remove(path)
                print(f"Removed: {path}")

    text = load_document(args.document)
    chunks = chunk_by_paragraph(text)
    store = index_chunks(chunks, storage_dir=args.storage_dir)
    demo_query(store, args.query, top_k=args.top_k)
    store.close()

    print(f"\nDone. Run the recipe:")
    print(f'  spl run cookbook/08_rag_query/rag_query.spl --adapter ollama question="{args.query}"')


if __name__ == "__main__":
    main()
