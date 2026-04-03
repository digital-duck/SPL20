"""
LangGraph equivalent of rag_query.spl

Pattern: CALL (index + retrieve, deterministic) + GENERATE (single LLM answer)

Key contrast with SPL:
  SPL's `rag.query(...)` call is a CALL — deterministic, zero LLM tokens.
  LangGraph has no such distinction; all nodes are Python functions.
  The programmer must manually track which nodes invoke the LLM.

Usage:
    pip install langgraph langchain-ollama langchain-community faiss-cpu
    python cookbook/08_rag_query/langgraph/rag_langgraph.py \\
        --doc /path/to/doc.md --question "Who is Wen?"
    python cookbook/08_rag_query/langgraph/rag_langgraph.py \\
        --doc /path/to/doc.md --question "What is Momagrid?" \\
        --model llama3.2 --embed-model nomic-embed-text
"""

import click
from pathlib import Path
from typing import TypedDict

from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph


# ── State ─────────────────────────────────────────────────────────────────────

class RagState(TypedDict):
    doc:         str
    question:    str
    model:       str
    embed_model: str
    log_dir:     str
    context:     str
    answer:      str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Nodes ─────────────────────────────────────────────────────────────────────

def node_index_retrieve(state: RagState) -> dict:
    # CALL rag.query(context.question, top_k=3) — deterministic, zero LLM tokens
    print(f"Indexing document | {state['doc']} ...")
    loader = TextLoader(state["doc"], encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = OllamaEmbeddings(model=state["embed_model"])
    store = FAISS.from_documents(chunks, embeddings)
    print(f"Retrieving context | top_k=3 ...")
    results = store.similarity_search(state["question"], k=3)
    context = "\n\n".join(r.page_content for r in results)
    return {"context": context}

def node_generate(state: RagState) -> dict:
    # GENERATE answer(question) — single LLM call
    print("Generating answer ...")
    prompt = (
        "You are a knowledgeable assistant. Use the provided context to answer accurately.\n\n"
        f"Context:\n{state['context']}\n\n"
        f"Question: {state['question']}\n\n"
        "Answer in plain prose."
    )
    answer = ChatOllama(model=state["model"]).invoke(prompt).content.strip()
    _write(f"{state['log_dir']}/answer.md", answer)
    return {"answer": answer}

def node_commit(state: RagState) -> dict:
    # COMMIT @answer WITH status = 'complete'
    _write(f"{state['log_dir']}/final.md", state["answer"])
    print("Committed | status=complete")
    return {}


# ── Graph ─────────────────────────────────────────────────────────────────────

def build_graph():
    g = StateGraph(RagState)
    g.add_node("index_retrieve", node_index_retrieve)
    g.add_node("generate",       node_generate)
    g.add_node("commit",         node_commit)
    g.set_entry_point("index_retrieve")
    g.add_edge("index_retrieve", "generate")
    g.add_edge("generate",       "commit")
    g.add_edge("commit",         END)
    return g.compile()


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--doc", required=True, help="Path to document to index")
@click.option("--question", required=True, help="Question to answer")
@click.option("--model", default="gemma3", help="Ollama chat model")
@click.option("--embed-model", default="nomic-embed-text", help="Ollama embedding model")
@click.option("--log-dir", default="cookbook/08_rag_query/langgraph/logs", help="Log directory")
def main(doc, question, model, embed_model, log_dir):
    """RAG Query — LangGraph edition"""
    result = build_graph().invoke({
        "doc":         doc,
        "question":    question,
        "model":       model,
        "embed_model": embed_model,
        "log_dir":     log_dir,
        "context":     "",
        "answer":      "",
    })
    print("\n" + "=" * 60)
    print(result["answer"])

if __name__ == "__main__":
    main()
