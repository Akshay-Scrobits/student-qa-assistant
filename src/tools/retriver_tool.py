"""
Module for retrieving context from the vector store.
"""
from logging import getLogger

from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config.settings import GOOGLE_API_KEY, DEFAULT_NAMESPACE
from utils.vector_db.index_strategies.pinecone_vector_index import PineconeVectorIndex
from utils.vector_db.loader_strategies.local_loader import LocalLoader
from utils.vector_db.vector_store_singleton import VectorStoreSingleton
from core.singletone_core import Singleton

logger = getLogger(__name__)


class ContextRetriever(Singleton):
    """
    Context retrieval service that manages vector store operations.

    Heavy objects (embeddings model, vector store, etc.) are initialized once
    in __init__ and reused across all requests for optimal performance.

    This class implements the Singleton pattern to ensure expensive resources
    are created only once during the application lifetime.
    """

    def __init__(self):
        """Initialize embeddings model and vector store components (one-time only)."""
        # Check if already initialized to prevent re-initialization
        if hasattr(self, "_initialized"):
            return

        logger.info(
            "Initializing ContextRetriever with embeddings model and vector store components..."
        )

        try:
            # Initialize embeddings model
            self.embeddings_model = GoogleGenerativeAIEmbeddings(
                model="models/gemini-embedding-001",
                google_api_key=GOOGLE_API_KEY,
                output_dimensionality=1024,
            )
            logger.info("Successfully initialized embeddings model")

            # Initialize document loader and vector index strategies
            self.document_loader_strategy = LocalLoader()
            self.vector_index_strategy = PineconeVectorIndex(
                embeddings=self.embeddings_model
            )
            logger.info("Successfully initialized loader and index strategies")

            # Initialize vector store
            self.vector_store = VectorStoreSingleton(
                embeddings_model=self.embeddings_model,
                document_loader_strategy=self.document_loader_strategy,
                vector_index_strategy=self.vector_index_strategy,
            )
            logger.info("Successfully initialized vector store")
            logger.info("ContextRetriever initialization complete")

            # Mark as initialized to prevent re-initialization
            self._initialized = True

        except Exception as e:
            logger.error("Failed to initialize ContextRetriever: %s", e)
            raise RuntimeError(f"ContextRetriever initialization failed: {str(e)}") from e

    async def retrieve_context(self, query_text: str, namespace: str = None) -> str:
        """
        Retrieve relevant context from documents for a given query.

        Args:
            query_text: User question in string format
            namespace: The namespace to query within (optional)

        Returns:
            Context related to user's question in string format

        Raises:
            ValueError: If query_text is empty or invalid
            RuntimeError: If vector store query fails
        """
        try:
            # Validate input
            if not query_text or not query_text.strip():
                logger.error("Empty or invalid query_text provided")
                raise ValueError("query_text cannot be empty")

            logger.info("DEBUG: retrieve_context namespace argument: %s", namespace)

            # Resolve namespace
            if not namespace:
                namespace = DEFAULT_NAMESPACE
                logger.warning(
                    "Namespace not provided, falling back to default: %s", namespace
                )

            # Execute query using the pre-initialized vector store
            try:
                result = await self.vector_store.query(
                    query_text=query_text, namespace=namespace
                )
                logger.info(
                    "Successfully retrieved context for query in namespace: %s", namespace
                )

                if not result:
                    logger.warning("Query returned empty result")
                    return "No relevant context found for the given query."

                return result
            except Exception as e:
                logger.error("Vector store query failed: %s", e)
                raise RuntimeError(f"Failed to query vector store: {str(e)}") from e

        except (ValueError, RuntimeError):
            # Re-raise known exceptions
            raise
        except Exception as e:
            # Catch any unexpected exceptions
            logger.error("Unexpected error in retrieve_context: %s", e, exc_info=True)
            raise RuntimeError(f"Unexpected error occurred: {str(e)}") from e


async def get_context(query_text: str, namespace: str = None) -> str:
    """
    MCP tool function to retrieve relevant context from documents.

    This function helps to answer user questions by retrieving relevant context from documents.

    Args:
        query_text: User question in string format
        namespace: The namespace to query within (optional)

    Returns:
        Context related to user's question in string format

    Raises:
        ValueError: If query_text is empty or invalid
        RuntimeError: If vector store initialization or query fails
    """
    return await ContextRetriever.get_instance().retrieve_context(
        query_text=query_text, namespace=namespace
    )
