"""
Evaluator agent module for assessing student answers.
"""
import re

from langchain_core.prompts import ChatPromptTemplate

from agents.base.base_agent import BaseAgent
from config.settings import BASE_DIR
from core.singletone_core import AsyncSingleton
from utils.yml_loader import load_yml
from schemas.workflow import WorkflowState


class EvaluatorAgent(AsyncSingleton, BaseAgent):
    """
    Evaluator agent that assesses student answers against reference answers.
    """

    def __init__(self):
        super().__init__()
        self.prompt = None

    async def _initialize(self):
        """Asynchronously load prompts and initialize the prompt template."""
        prompts = await load_yml(f"{BASE_DIR}/src/prompts/evaluator_agent.yml")
        self.prompt = ChatPromptTemplate.from_template(prompts["evaluator_system"])

    async def call_llm(self, state: WorkflowState) -> dict:
        """
        Node function for the evaluator agent.

        Evaluates the student's answer using the reference answer and context.
        """
        chain = self.prompt | self.llm

        input_data = {
            "question": state["question"],
            "reference_answer": state["reference_answer"],
            "student_answer": state["student_answer"],
        }

        response = await chain.ainvoke(input_data)

        # Parse JSON response
        try:
            data = self._parse_json_response(response.content)
            # Ensure we return a dict that always has at least an 'error' or valid keys
            evaluation = {
                "score": data.get("score"),
                "confidence": data.get("confidence"),
                "feedback": data.get("feedback"),
                "improvements": data.get("improvements"),
            }
            return {"evaluation": evaluation, "messages": [response]}
        except (ValueError, KeyError) as e:
            # Fallback for manual score extraction if JSON fails
            score = None
            if "score" in response.content.lower():
                match = re.search(r'"score":\s*(\d+)', response.content)
                if match:
                    score = int(match.group(1))

            return {
                "evaluation": {
                    "score": score,
                    "feedback": (
                        response.content
                        if not score
                        else f"Grading failed but here is the raw output: {response.content}"
                    ),
                    "error": f"Parsing failed: {str(e)}",
                    "raw_output": response.content,
                },
                "messages": [response],
            }
