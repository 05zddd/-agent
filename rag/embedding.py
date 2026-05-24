from typing import List
from langchain_community.embeddings import DashScopeEmbeddings
from backend.config import get_settings

settings = get_settings()


class EmbeddingService:
    """Generate embeddings using DashScope text-embedding-v4."""

    def __init__(self):
        self.model = DashScopeEmbeddings(
            model=settings.embedding_model,
            dashscope_api_key=settings.dashscope_api_key,
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        return self.model.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a single query.

        Args:
            query: Query string

        Returns:
            Embedding vector
        """
        return self.model.embed_query(query)


_embedding_instance: EmbeddingService = None


def get_embedding() -> EmbeddingService:
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = EmbeddingService()
    return _embedding_instance
