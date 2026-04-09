"""
Tutor agent module for generating questions and tutoring students.
"""
from langchain_core.prompts import ChatPromptTemplate

from agents.base.base_agent import BaseAgent
from config.settings import BASE_DIR
from core.singletone_core import AsyncSingleton
from utils.yml_loader import load_yml
from schemas.workflow import WorkflowState


class TutorAgent(AsyncSingleton, BaseAgent):
    """
    Tutor agent that interacts with students and generates questions.
    """

    def __init__(self):
        super().__init__()
        self.prompt = None

    async def _initialize(self):
        """Asynchronously load prompts and initialize the prompt template."""
        prompts = await load_yml(f"{BASE_DIR}/src/prompts/tutor_agent.yml")
        self.prompt = ChatPromptTemplate.from_template(prompts["tutor_system"])

    async def call_llm(self, state: WorkflowState) -> dict:
        """
        Node function for the tutor agent.

        Generates a question or response based on the current context and history.
        """
        chain = self.prompt | self.llm
        last_message = (
            state.get("messages", [])[-1].content if state.get("messages") else ""
        )
        response = await chain.ainvoke(
            {
                "context": state.get("context", "No context provided"),
                "last_message": last_message,
            }
        )

        # Parse JSON response
        try:
            data = self._parse_json_response(response.content)
            question = data.get("question", "No question generated.")
            ref_answer = data.get("reference_answer", "No reference answer generated.")

            return {
                "messages": [response],
                "question": question,
                "reference_answer": ref_answer,
                "context": state.get("context"),
            }
        except (ValueError, KeyError):
            # Fallback if parsing fails
            return {
                "messages": [response],
                "question": response.content,
                "reference_answer": "Error parsing reference answer from AI.",
                "context": state.get("context"),
            }
