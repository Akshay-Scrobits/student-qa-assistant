"""
Service for uploading and indexing files into Pinecone vector database.
Uses docling for document conversion and semantic chunking via VectorStoreSingleton.
"""

import asyncio
from io import BytesIO
from logging import getLogger

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import DocumentStream

from tools.retriver_tool import ContextRetriever
from core.thread_safe_singletone import ThreadSafeSingletonCore

logger = getLogger(__name__)


class VectorDBUploadService(ThreadSafeSingletonCore):
    """
    Service to handle file uploads and indexing into Pinecone using docling.
    Implemented as a thread-safe singleton.
    """

    def __init__(self):
        # We check _initialized because __init__ might be called multiple times
        # depending on how ThreadSafeSingletonCore is used.
        if hasattr(self, "_initialized"):
            return

        self.retriever = ContextRetriever.get_instance()
        self.converter = DocumentConverter()
        self._initialized = True

    async def convert_to_markdown(self, file_content: bytes, file_name: str) -> str:
        """
        This method is used to convert a document file to markdown using docling.
        Runs the blocking conversion in a thread pool to avoid blocking the event loop.

        Args:
            file_content: Binary content of the document.
            file_name: Name of the file (used for format inference).

        Returns:
            Extracted markdown text.
        """
        loop = asyncio.get_running_loop()

        def convert():
            # docling requires a DocumentStream or path. DocumentStream takes a stream and a name.
            buf = BytesIO(file_content)
            source = DocumentStream(name=file_name, stream=buf)
            result = self.converter.convert(source)
            return result.document.export_to_markdown()

        return await loop.run_in_executor(None, convert)

    async def upload_and_index_file(
        self, file_content: bytes, file_name: str, namespace: str
    ) -> bool:
        """
        Uploads a file, converts it to Markdown using docling, and indexes it.

        Args:
            file_content: Bytes of the uploaded file
            file_name: Name of the file (to determine type)
            namespace: Namespace for data isolation in Pinecone

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(
                "Processing in-memory file: %s for namespace: %s",
                file_name,
                namespace
            )

            # 1. Convert to Markdown using docling (handling bytes via DocumentStream)
            markdown_text = await self.convert_to_markdown(file_content, file_name)

            if not markdown_text:
                logger.warning("No content extracted from file: %s", file_name)
                return False

            # 2. Ingest into Vector Store
            # This uses the SemanticChunker defined in VectorStoreSingleton
            await self.retriever.vector_store.ingest_document(
                text=markdown_text, namespace=namespace
            )

            logger.info("Successfully indexed %s into namespace: %s", file_name, namespace)
            return True

        # pylint: disable=broad-exception-caught
        except Exception as e:
            logger.error(
                "Failed to upload and index file %s: %s",
                file_name,
                str(e),
                exc_info=True
            )
            return False
