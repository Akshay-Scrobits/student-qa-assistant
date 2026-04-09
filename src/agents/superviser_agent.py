"""
Supervisor agent module for coordinating the tutoring workflow.
"""
from typing import Literal

from langchain_core.prompts import ChatPromptTemplate

from agents.base.base_agent import BaseAgent
from config.settings import BASE_DIR
from core.singletone_core import AsyncSingleton
from utils.yml_loader import load_yml
from schemas.workflow import WorkflowState


class SuperviserAgent(AsyncSingleton, BaseAgent):
    """
    Supervisor agent that decides the next node in the conversation graph.
    """

    def __init__(self):
        super().__init__()
        self.prompt = None

    async def _initialize(self):
        """Asynchronously load prompts and initialize the prompt template."""
        prompts = await load_yml(f"{BASE_DIR}/src/prompts/superviser_agent.yml")
        self.prompt = ChatPromptTemplate.from_template(prompts["supervisor_system"])

    async def call_llm(self, state: WorkflowState) -> dict:
        """
        Node function for the supervisor agent.

        Determines if the student needs more tutoring or an evaluation.
        """
        chain = self.prompt | self.llm

        # Get last message content
        last_message = state["messages"][-1].content if state["messages"] else ""

        response = await chain.ainvoke(
            {
                "context": state.get("context", "No context provided"),
                "last_message": last_message,
            }
        )

        next_node = response.content.strip().lower()
        if next_node not in ["tutor", "evaluator", "end"]:
            next_node = "tutor"  # Default fallback

        return {"next_node": next_node, "messages": [response]}

    def router(self, _state: WorkflowState) -> Literal["tutor", "evaluator", "end"]:
        """Determines the next step after supervision."""
        return _state.get("next_node", "end")
