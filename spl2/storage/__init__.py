"""SPL 2.0 storage backends."""

from spl2.storage.memory import MemoryStore


def get_vector_store(backend: str = "faiss", storage_dir: str = ".spl",
                     embedding_model: str | None = None, **kwargs):
    """Factory for vector store backends.

    Parameters
    ----------
    backend : str
        Currently only ``"faiss"`` is supported.
    storage_dir : str
        Directory for persisting index and metadata files.
    **kwargs
        Forwarded to the vector store constructor (e.g. ``embedding_dim``,
        ``embedding_fn``).

    Returns
    -------
    VectorStore
        An initialised vector store instance.

    Raises
    ------
    ImportError
        If the required backend library is not installed.
    ValueError
        If an unknown backend is requested.
    """
    if backend == "faiss":
        try:
            from spl2.storage.vector import VectorStore
        except ImportError as exc:
            raise ImportError(
                "FAISS vector store requires numpy and faiss-cpu. "
                "Install them with: pip install numpy faiss-cpu"
            ) from exc
        return VectorStore(storage_dir=storage_dir, embedding_model=embedding_model, **kwargs)
    raise ValueError(f"Unknown vector store backend: {backend!r}. Supported: 'faiss'")
