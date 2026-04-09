"""
Pinecone vector index strategy for storing and querying embeddings.

This module implements the VectorIndexStrategy interface for Pinecone,
handling document chunking, embedding, and semantic search operations.
"""

import asyncio
import uuid
from logging import getLogger

# pylint: disable=no-name-in-module
from pinecone import Pinecone, ServerlessSpec

from config.settings import (
    PINECONE_API_KEY,
    PINECONE_INDEX_NAME,
    PINECONE_REGION,
    PINECONE_CLOUD,
    PINECONE_METRIC,
    require_setting,
)
from utils.vector_db.index_strategies.base import VectorIndexStrategy

logger = getLogger(__name__)


class PineconeVectorIndex(VectorIndexStrategy):
    """Pinecone implementation of the VectorIndexStrategy."""

    def __init__(self, embeddings):
        """Initialize Pinecone index with embeddings model."""
        collection_name = require_setting(PINECONE_INDEX_NAME, "PINECONE_INDEX_NAME")
        api_key = require_setting(PINECONE_API_KEY, "PINECONE_API_KEY")

        self.__collection_name = collection_name
        self.__pinecone = Pinecone(api_key=api_key)
        self.__embeddings = embeddings
        self.__region = PINECONE_REGION or "us-east-1"

    async def _ensure_index_exists(self):
        """Checks if the index exists, and creates it if not."""
        available_indexes = [index.name for index in self.__pinecone.list_indexes()]
        if self.__collection_name not in available_indexes:
            logger.info(
                "Creating serverless Pinecone index: %s", self.__collection_name
            )
            self.__pinecone.create_index(
                name=self.__collection_name,
                dimension=1024,
                metric=PINECONE_METRIC,
                spec=ServerlessSpec(cloud=PINECONE_CLOUD, region=self.__region),
            )

            # Wait for index to be ready
            while not self.__pinecone.describe_index(self.__collection_name).status[
                "ready"
            ]:
                logger.info(
                    "Waiting for index %s to be ready...", self.__collection_name
                )
                await asyncio.sleep(1)
            logger.info("Index %s is ready.", self.__collection_name)

    async def create_or_load_vector_index(
        self, markdown_text: str, chunker=None, namespace: str = None
    ):
        """
        Create or load vector index with document chunks.

        Args:
            markdown_text: The document text to index
            chunker: Optional callable for chunking text
            namespace: Namespace for data isolation
        """
        # Note: We removed the self.__collection check because we want to
        # allow multiple uploads to different namespaces

        # Ensure index exists before trying to access it
        await self._ensure_index_exists()

        index = self.__pinecone.Index(self.__collection_name)
        # Use provided chunker callable if supplied; it may return Documents or strings
        if chunker is not None:
            # Run chunker in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            chunk_outputs = await loop.run_in_executor(None, chunker, markdown_text)
            if chunk_outputs and hasattr(chunk_outputs[0], "page_content"):
                chunk_texts = [c.page_content for c in chunk_outputs]
            else:
                chunk_texts = list(chunk_outputs)
        else:
            # Fallback: no chunker provided; treat whole markdown as a single chunk
            chunk_texts = [markdown_text] if markdown_text else []
        if not chunk_texts:
            return self

        # Embed documents using langchain's HuggingFaceEmbeddings
        # Run embedding in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        vectors = await loop.run_in_executor(
            None, self.__embeddings.embed_documents, chunk_texts
        )
        pinecone_vectors = []
        for i, (values, chunk_text) in enumerate(zip(vectors, chunk_texts)):
            # Use UUID to ensure unique IDs across multiple uploads
            chunk_id = str(uuid.uuid4())
            pinecone_vectors.append(
                {
                    "id": chunk_id,
                    "values": values,
                    "metadata": {
                        "chunk_text": chunk_text,
                        "chunk_id": i,
                        "source": "uploaded_document",
                    },
                }
            )

        # Upsert to Pinecone with namespace (run in thread pool)
        await loop.run_in_executor(
            None, lambda: index.upsert(vectors=pinecone_vectors, namespace=namespace)
        )
        logger.info(
            "Uploaded %d chunks to Pinecone index '%s' in namespace '%s'",
            len(pinecone_vectors),
            self.__collection_name,
            namespace,
        )
        return self

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
        if namespace is None:
            raise ValueError(
                "Namespace is required for semantic search to ensure data isolation."
            )

        # Ensure index exists before trying to access it
        await self._ensure_index_exists()

        index = self.__pinecone.Index(self.__collection_name)

        # Query both user namespace and admin namespace
        namespaces_to_query = [namespace, "admin"]
        response = index.query_namespaces(
            metric="cosine",
            vector=embeded_query,
            namespaces=namespaces_to_query,
            top_k=20,
            include_metadata=True,
        )

        # Handle both dict-like and object responses
        matches = None
        if isinstance(response, dict):
            matches = response.get("matches")
        else:
            matches = getattr(response, "matches", None)

        if not matches:
            return "No relevant context found for the question."

        # Combine context from top matches (could be from user or admin namespace)
        context_parts = []
        for match in matches[:5]:  # Take top 5 results
            metadata = getattr(match, "metadata", None)
            if metadata is None and isinstance(match, dict):
                metadata = match.get("metadata", {})
            chunk_text = (
                metadata.get("chunk_text", "") if isinstance(metadata, dict) else ""
            )
            if chunk_text:
                context_parts.append(chunk_text)

        if context_parts:
            return "\n\n---\n\n".join(context_parts)
        return "No relevant context found for the question."
