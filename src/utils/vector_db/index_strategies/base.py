"""
Abstract base class for vector index strategies.

This module defines the interface for vector index implementations.
"""

from abc import ABC, abstractmethod


class VectorIndexStrategy(ABC):
    """Abstract base class for vector index strategies."""

    @abstractmethod
    async def create_or_load_vector_index(
        self, markdown_text: str, chunker=None, namespace: str = None
    ):
        """
        Create or load a vector index with document chunks.

        Args:
            markdown_text: The document text to index
            chunker: Optional callable for chunking text
            namespace: Namespace for data isolation
        """

    @abstractmethod
    async def semantic_search(
        self, embeded_query: list[float], namespace: str = None
    ) -> str:
        """
        Perform semantic search in the vector index.

        Args:
            embeded_query: The embedded query vector
            namespace: Namespace to search in

        Returns:
            Relevant document chunk text
        """
