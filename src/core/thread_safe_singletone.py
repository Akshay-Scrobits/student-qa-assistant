"""
Core module for thread-safe singleton pattern implementation.
"""

import threading


# pylint: disable=too-few-public-methods
class ThreadSafeSingletonCore:
    """
    A thread-safe implementation of the Singleton pattern.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of the class.
        """
        return cls()
