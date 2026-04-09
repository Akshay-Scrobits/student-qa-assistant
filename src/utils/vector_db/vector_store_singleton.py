"""
Vector store singleton for managing document embeddings and queries.

This module provides a singleton class for managing the vector store,
including document ingestion and semantic search operations.
"""

import asyncio
from logging import getLogger

from langchain_experimental.text_splitter import SemanticChunker

from utils.vector_db.index_strategies.base import VectorIndexStrategy
from utils.vector_db.loader_strategies.base import DocumentLoaderStrategy

logger = getLogger(__name__)


class VectorStoreSingleton:
    """
    Singleton class for managing the vector store.

    Handles document loading, chunking, embedding, and querying operations
    with support for namespace-based data isolation.
    """

    _instance = None

    vector_store = None

    def __new__(cls, *args, **kwargs):
        """Standard singleton __new__ implementation."""
        if cls._instance is None:
            cls._instance = super(VectorStoreSingleton, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        embeddings_model,
        document_loader_strategy: DocumentLoaderStrategy,
        vector_index_strategy: VectorIndexStrategy,
    ):
        """Initialize all components of the vector store (one-time only)."""
        if not hasattr(self, "_initialized"):
            self.embeddings_model = embeddings_model
            self.document_loader_strategy = document_loader_strategy
            self.vector_index_strategy = vector_index_strategy
            self.text_splitter = SemanticChunker(
                embeddings_model, breakpoint_threshold_type="percentile"
            )

            def semantic_chunker(markdown_text: str):
                return self.text_splitter.create_documents([markdown_text])

            self.chunker = semantic_chunker
            self._initialized = True

    def _build_vectorstore(self):
        """
        Orchestrate the document loading and vector store creation.

        Deprecated: We are now using dynamic ingestion via /upload.
        If we need to initialize the vector store connection,
        we can do it here without loading files.
        """
        if self.vector_store is None:
            # Just ensure the strategy is ready (e.g. Pinecone index connected)
            # We don't need to load files from disk anymore
            pass
        return self.vector_store

    async def ingest_document(self, text: str, namespace: str = None):
        """
        Ingest a document text into the vector store for a specific namespace.

        Args:
            text: The document text to ingest
            namespace: The namespace for data isolation
        """
        logger.info("--- Ingesting Document for Namespace: %s ---", namespace)
        await self.vector_index_strategy.create_or_load_vector_index(
            text, chunker=self.chunker, namespace=namespace
        )
        logger.info("--- Document Ingested Successfully ---")

    async def query(self, query_text: str, namespace: str = None):
        """
        Query the vector store for relevant documents.

        Args:
            query_text: The query string
            namespace: The namespace to search in

        Returns:
            Relevant document chunks from the vector store
        """
        # HuggingFaceEmbeddings from langchain exposes embed_query for
        # single strings
        # Run embedding in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        query_embedding = await loop.run_in_executor(
            None, self.embeddings_model.embed_query, query_text
        )
        # We don't need to auto-build vectorstore anymore as we rely on
        # uploaded data
        results = await self.vector_index_strategy.semantic_search(
            embeded_query=query_embedding,
            namespace=namespace,
        )
        return results
