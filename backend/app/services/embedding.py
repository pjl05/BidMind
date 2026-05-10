from typing import Optional
import hashlib
import numpy as np


class EmbeddingService:
    """Simple embedding service using hash-based representation."""

    def __init__(self):
        self.dimension = 1536

    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for text.

        Note: For production, use a dedicated embedding model.
        This is a placeholder that uses hash-based representation.
        """
        text_hash = hashlib.sha256(text.encode()).digest()
        vector = np.frombuffer(text_hash[:self.dimension], dtype=np.float32)
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    async def embed_documents(self, documents: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        return [await self.embed_text(doc) for doc in documents]


embedding_service = EmbeddingService()