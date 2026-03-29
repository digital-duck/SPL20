"""
AutoGen equivalent of rag_query.spl

Pattern: deterministic CALL (index + retrieve) + single LLM GENERATE

AutoGen's ConversableAgent handles the LLM generation step. The retrieval
pipeline (FAISS index + similarity search) is plain Python — a CALL in SPL
terms. AutoGen has no language-level distinction between the two.

Usage:
    pip install pyautogen langchain-ollama langchain-community faiss-cpu
    python cookbook/08_rag_query/autogen/rag_autogen.py \\
        --doc /path/to/doc.md --question "Who is Wen?"
    python cookbook/08_rag_query/autogen/rag_autogen.py \\
        --doc /path/to/doc.md --question "What is Momagrid?" \\
        --model llama3.2 --embed-model nomic-embed-text
"""

import argparse
from pathlib import Path

from autogen import ConversableAgent
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_ollama import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")

def _build_index(doc_path: str, embed_model: str) -> FAISS:
    # CALL — deterministic, zero LLM tokens in SPL terms
    loader = TextLoader(doc_path, encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(docs)
    embeddings = OllamaEmbeddings(model=embed_model)
    return FAISS.from_documents(chunks, embeddings)

def _retrieve(store: FAISS, question: str, k: int = 3) -> str:
    # CALL rag.query(context.question, top_k=3) — deterministic, zero LLM tokens
    results = store.similarity_search(question, k=k)
    return "\n\n".join(r.page_content for r in results)


# ── Main runner ───────────────────────────────────────────────────────────────

def run(doc: str, question: str, model: str, embed_model: str, log_dir: str) -> str:
    llm_config = {
        "config_list": [{
            "model":    model,
            "base_url": "http://localhost:11434/v1",
            "api_key":  "ollama",
        }]
    }

    # CALL index + retrieve — deterministic
    print(f"Indexing document | {doc} ...")
    store = _build_index(doc, embed_model)
    print(f"Retrieving context | top_k=3 ...")
    context = _retrieve(store, question)

    # GENERATE answer — single LLM call
    print("Generating answer ...")
    proxy = ConversableAgent("proxy", llm_config=False, human_input_mode="NEVER")
    assistant = ConversableAgent(
        "Assistant",
        system_message="You are a knowledgeable assistant. Use the provided context to answer accurately.",
        llm_config=llm_config,
        human_input_mode="NEVER",
        max_consecutive_auto_reply=1,
    )
    message = (
        f"Context:\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer in plain prose."
    )
    result = proxy.initiate_chat(assistant, message=message, max_turns=1)
    answer = result.chat_history[-1]["content"]

    # COMMIT @answer WITH status = 'complete'
    _write(f"{log_dir}/answer.md", answer)
    _write(f"{log_dir}/final.md", answer)
    print("Committed | status=complete")
    return answer


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="RAG Query — AutoGen edition")
    p.add_argument("--doc",         required=True,              help="Path to document to index")
    p.add_argument("--question",    required=True,              help="Question to answer")
    p.add_argument("--model",       default="gemma3",           help="Ollama chat model")
    p.add_argument("--embed-model", default="nomic-embed-text", help="Ollama embedding model")
    p.add_argument("--log-dir",     default="cookbook/08_rag_query/autogen/logs")
    args = p.parse_args()

    answer = run(args.doc, args.question, args.model, args.embed_model, args.log_dir)
    print("\n" + "=" * 60)
    print(answer)

if __name__ == "__main__":
    main()
