"""Tests for SPL 2.0 storage — memory store and vector store."""

import os
import tempfile
import pytest
from spl2.storage.memory import MemoryStore


class TestMemoryStore:
    def test_set_get(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            store.set("key1", "value1")
            assert store.get("key1") == "value1"
            store.close()

    def test_get_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            assert store.get("nonexistent") is None
            store.close()

    def test_delete(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            store.set("key1", "value1")
            assert store.delete("key1") is True
            assert store.get("key1") is None
            assert store.delete("key1") is False
            store.close()

    def test_list_keys(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            store.set("a", "1")
            store.set("b", "2")
            keys = store.list_keys()
            assert "a" in keys
            assert "b" in keys
            store.close()

    def test_cache_get_set(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            assert store.cache_get("hash1") is None
            store.cache_set("hash1", "cached_result", model="echo")
            assert store.cache_get("hash1") == "cached_result"
            store.close()

    def test_overwrite(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = MemoryStore(f"{tmpdir}/memory.db")
            store.set("key", "v1")
            store.set("key", "v2")
            assert store.get("key") == "v2"
            store.close()


class TestVectorStore:
    """Test FAISS vector store if numpy and faiss are available."""

    @pytest.fixture
    def store(self):
        try:
            from spl2.storage.vector import VectorStore
        except ImportError:
            pytest.skip("numpy or faiss-cpu not installed")

        with tempfile.TemporaryDirectory() as tmpdir:
            s = VectorStore(storage_dir=tmpdir)
            yield s
            s.close()

    def test_add_and_count(self, store):
        assert store.count() == 0
        doc_id = store.add("Python is a programming language")
        assert doc_id >= 1
        assert store.count() == 1

    def test_add_batch(self, store):
        ids = store.add_batch(
            ["first document", "second document", "third document"],
            [{"idx": 0}, {"idx": 1}, {"idx": 2}],
        )
        assert len(ids) == 3
        assert store.count() == 3

    def test_query(self, store):
        store.add("Python is a programming language", {"source": "wiki"})
        store.add("JavaScript runs in browsers", {"source": "wiki"})
        store.add("Rust is a systems language", {"source": "wiki"})

        results = store.query("What programming language is like C?", top_k=2)
        assert len(results) <= 2
        assert all("text" in r for r in results)
        assert all("score" in r for r in results)

    def test_query_empty_store(self, store):
        results = store.query("anything", top_k=5)
        assert results == []

    def test_delete(self, store):
        doc_id = store.add("test doc")
        assert store.delete(doc_id) is True
        # Metadata deleted, but FAISS index still has the vector
        assert store.delete(999) is False


class TestGetVectorStore:
    def test_unknown_backend(self):
        from spl2.storage import get_vector_store
        with pytest.raises(ValueError, match="Unknown"):
            get_vector_store("unknown_backend")

    def test_faiss_backend(self):
        try:
            from spl2.storage import get_vector_store
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                store = get_vector_store("faiss", tmpdir)
                assert store.count() == 0
                store.close()
        except ImportError:
            pytest.skip("faiss-cpu not installed")
