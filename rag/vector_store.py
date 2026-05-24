import os
from typing import List, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.config import get_settings

settings = get_settings()


class VectorStore:
    """ChromaDB vector store for document retrieval."""

    def __init__(self, collection_name: str = "documents"):
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self.collection_name = collection_name
        self._ensure_collection()

    def _ensure_collection(self):
        try:
            self.collection = self.client.get_collection(self.collection_name)
        except Exception:
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )

    def add_documents(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: List[dict] = None,
        ids: List[str] = None,
    ):
        """Add documents to the vector store.

        Args:
            texts: Document text chunks
            embeddings: Corresponding embedding vectors
            metadatas: Metadata for each chunk
            ids: Unique IDs for each chunk (auto-generated if not provided)
        """
        if not ids:
            count = self.collection.count()
            ids = [f"doc_{count + i}" for i in range(len(texts))]

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas or [{}] * len(texts),
        )

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]:
        """Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results

        Returns:
            List of {"text": str, "metadata": dict, "distance": float}
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["documents"] and results["documents"][0]:
            for i in range(len(results["documents"][0])):
                output.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else 0.0,
                })
        return output

    def delete_by_session(self, session_id: str):
        """Delete all documents belonging to a session."""
        try:
            docs = self.collection.get(
                where={"session_id": session_id},
                include=["metadatas"],
            )
            if docs and docs["ids"]:
                self.collection.delete(ids=docs["ids"])
        except Exception:
            pass

    def get_collection_stats(self) -> dict:
        """Get collection statistics."""
        return {
            "name": self.collection_name,
            "count": self.collection.count(),
        }

    def clear(self):
        """Delete all documents from the collection."""
        self.client.delete_collection(self.collection_name)
        self._ensure_collection()


_vector_store_instance: Optional[VectorStore] = None


def get_vector_store(collection: str = "documents") -> VectorStore:
    global _vector_store_instance
    if _vector_store_instance is None or _vector_store_instance.collection_name != collection:
        _vector_store_instance = VectorStore(collection)
    return _vector_store_instance
