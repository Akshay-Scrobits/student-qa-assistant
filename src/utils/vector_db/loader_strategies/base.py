"""
Abstract base class for document loader strategies.

This module defines the interface for document loader implementations.
"""

from abc import ABC, abstractmethod


# pylint: disable=too-few-public-methods
class DocumentLoaderStrategy(ABC):
    """Abstract base class for document loader strategies."""

    @abstractmethod
    def load_documents(self, path) -> str:
        """
        Load documents from the specified path.

        Args:
            path: Path to the document(s)

        Returns:
            The loaded document text
        """
