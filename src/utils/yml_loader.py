"""
Module for loading YAML files asynchronously.
"""

import aiofiles
from yaml import safe_load


async def load_yml(file_path: str) -> dict:
    """
    Load a YAML file from the specified path asynchronously.
    """
    async with aiofiles.open(file_path, "r") as file:
        content = await file.read()
        return safe_load(content)
