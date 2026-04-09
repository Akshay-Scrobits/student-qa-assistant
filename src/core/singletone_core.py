"""
Core module for singleton pattern implementation.
"""


# pylint: disable=too-few-public-methods
class Singleton:
    """
    A simple implementation of the Singleton pattern (synchronous).
    Uses a class-level dictionary to store instances per class.
    """

    _instances = {}

    def __new__(cls, *_args, **_kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

    @classmethod
    def get_instance(cls):
        """
        Returns the singleton instance of the class.
        """
        return cls()


class AsyncSingleton:
    """
    A base class for asynchronous singletons.
    Uses a class-level dictionary to store instances per class.
    Each subclass is guaranteed to have its own unique instance.
    """

    _instances = {}

    def __new__(cls, *_args, **_kwargs):
        if cls not in AsyncSingleton._instances:
            AsyncSingleton._instances[cls] = super().__new__(cls)
        return AsyncSingleton._instances[cls]

    @classmethod
    async def get_instance(cls):
        """
        Returns the singleton instance, initializing it asynchronously if needed.
        """
        # Ensure registry is accessed from the base class to avoid MRO leakage
        registry = AsyncSingleton._instances

        if cls not in registry:
            # Creation of instance will trigger __new__ which sets registry
            instance = cls()
            if hasattr(instance, "_initialize"):
                # pylint: disable=protected-access
                await instance._initialize()

        return registry[cls]
