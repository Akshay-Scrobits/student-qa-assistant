"""
Base module for agent definitions.
"""
import json
from typing import Any, Dict

from langchain.chat_models import init_chat_model

from config.settings import MODEL_NAME, TEMPERATURE, MODEL_PROVIDER


# pylint: disable=too-few-public-methods
class BaseAgent:
    """
    Abstract base class for all agents.
    Provides shared logic for LLM initialization and JSON parsing.
    """

    def __init__(self):
        """Initialize common LLM properties."""
        self.llm = init_chat_model(
            model=MODEL_NAME,
            model_provider=MODEL_PROVIDER,
            temperature=TEMPERATURE,
        )
        self.prompt = None

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Extracts and parses JSON from a string response.
        Handles markdown blocks.
        """
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except (json.JSONDecodeError, IndexError) as e:
            raise ValueError(f"Failed to parse JSON from AI response: {str(e)}") from e
