"""
Local document loader strategy.

This module provides a document loader implementation for local files.
Currently deprecated in favor of dynamic document upload.
"""

from utils.vector_db.loader_strategies.base import DocumentLoaderStrategy


# pylint: disable=too-few-public-methods
class LocalLoader(DocumentLoaderStrategy):
    """Local file document loader (deprecated)."""

    def load_documents(self, path):
        """
        Load documents from local path.

        Args:
            path: Path to the document

        Raises:
            NotImplementedError: This method is no longer supported
        """
        raise NotImplementedError(
            "Docling dependency removed. Local loading not supported."
        )
