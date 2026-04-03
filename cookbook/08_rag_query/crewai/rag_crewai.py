"""
CrewAI equivalent of rag_query.spl

Pattern: @tool wraps deterministic retrieval; single LLM Agent generates answer.

CrewAI has no CALL/GENERATE distinction — the Agent's ReAct loop handles both
tool calls (retrieval) and LLM reasoning (answer generation) uniformly.
The programmer cannot enforce at the language level that retrieval is deterministic.

Usage:
    pip install crewai langchain-ollama langchain-community faiss-cpu
    python cookbook/08_rag_query/crewai/rag_crewai.py \\
        --doc /path/to/doc.md --question "Who is Wen?"
    python cookbook/08_rag_query/crewai/rag_crewai.py \\
        --doc /path/to/doc.md --question "What is Momagrid?" \\
        --model llama3.2 --embed-model nomic-embed-text
"""

import click
from pathlib import Path

from crewai import Agent, Crew, Task
from crewai.tools import tool
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ── Index (module-level, built once per run) ──────────────────────────────────

_store: FAISS | None = None

def _build_index(doc_path: str, embed_model: str) -> None:
    global _store
    loader = TextLoader(doc_path, encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = OllamaEmbeddings(model=embed_model)
    _store = FAISS.from_documents(chunks, embeddings)


# ── Tool ──────────────────────────────────────────────────────────────────────

@tool("retrieve_context")
def retrieve_context_tool(question: str) -> str:
    """Retrieve the most relevant document passages for a question. Input: question string."""
    # CALL rag.query(context.question, top_k=3) — deterministic, zero LLM tokens in SPL
    if _store is None:
        return "Error: index not built"
    results = _store.similarity_search(question, k=3)
    return "\n\n".join(r.page_content for r in results)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")


# ── Main runner ───────────────────────────────────────────────────────────────

def run(doc: str, question: str, model: str, embed_model: str, log_dir: str) -> str:
    # CALL index — deterministic setup
    print(f"Indexing document | {doc} ...")
    _build_index(doc, embed_model)

    llm = ChatOllama(model=model)

    analyst = Agent(
        role="Research Assistant",
        goal="Retrieve relevant context from indexed documents and answer questions accurately",
        backstory="Expert at searching document collections and synthesizing precise answers.",
        tools=[retrieve_context_tool],
        llm=llm,
        verbose=False,
    )

    task = Task(
        description=(
            f"Answer the following question using the retrieve_context tool:\n\n"
            f"Question: {question}\n\n"
            "Steps:\n"
            "1. Use retrieve_context to find relevant passages\n"
            "2. Write a clear, accurate answer in plain prose based on the retrieved context\n\n"
            "If the context does not contain enough information, say so briefly."
        ),
        expected_output="A concise, accurate answer in plain prose based on retrieved context.",
        agent=analyst,
    )

    # GENERATE answer — via agent LLM
    print("Generating answer ...")
    crew = Crew(agents=[analyst], tasks=[task], verbose=False)
    result = crew.kickoff()
    answer = str(result)

    # COMMIT @answer WITH status = 'complete'
    _write(f"{log_dir}/answer.md", answer)
    _write(f"{log_dir}/final.md", answer)
    print("Committed | status=complete")
    return answer


# ── Entry point ───────────────────────────────────────────────────────────────

@click.command()
@click.option("--doc", required=True, help="Path to document to index")
@click.option("--question", required=True, help="Question to answer")
@click.option("--model", default="gemma3", help="Ollama chat model")
@click.option("--embed-model", default="nomic-embed-text", help="Ollama embedding model")
@click.option("--log-dir", default="cookbook/08_rag_query/crewai/logs", help="Log directory")
def main(doc, question, model, embed_model, log_dir):
    """RAG Query — CrewAI edition"""
    result = run(doc, question, model, embed_model, log_dir)
    print("\n" + "=" * 60)
    print(result)


if __name__ == "__main__":
    main()
