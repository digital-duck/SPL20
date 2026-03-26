"""SPL 2.0 storage backends."""

from spl.storage.memory import MemoryStore


def get_vector_store(
    backend: str = "faiss",
    storage_dir: str = ".spl",
    embedding_model: str | None = None,
    embed_provider: str = "sentence_transformers",
    **kwargs,
):
    """Factory for vector store backends.

    Parameters
    ----------
    backend : str
        One of ``"faiss"`` (default), ``"in_memory"``, ``"chroma"``, ``"qdrant"``.
        All backends use dd-vectordb under the hood.
    storage_dir : str
        Directory for persisting index and config files.
    embedding_model : str | None
        Embedding model name passed to dd-embed (e.g. ``"all-MiniLM-L6-v2"``).
    embed_provider : str
        dd-embed provider (default ``"sentence_transformers"``).
        Override to ``"ollama"``, ``"openai"``, etc.
    **kwargs
        Forwarded to the vector store constructor.

    Returns
    -------
    VectorStore
        An initialised vector store instance.
    """
    if backend in ("faiss", "in_memory", "chroma", "qdrant"):
        from spl.storage.vector import VectorStore
        return VectorStore(
            storage_dir=storage_dir,
            embedding_model=embedding_model,
            embed_provider=embed_provider,
            **kwargs,
        )
    raise ValueError(
        f"Unknown vector store backend: {backend!r}. "
        "Supported: 'faiss', 'in_memory', 'chroma', 'qdrant'"
    )
