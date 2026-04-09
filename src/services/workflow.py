"""
Workflow service module for coordinating the tutoring session and assessment.
"""
import logging
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from agents.superviser_agent import SuperviserAgent
from agents.tutor_agent import TutorAgent
from agents.evaluator_agent import EvaluatorAgent
from core.singletone_core import AsyncSingleton
from models.question import Question
from schemas.workflow import WorkflowState
from tools.retriver_tool import ContextRetriever


class WorkflowService(AsyncSingleton):
    """
    Service class to manage the LangGraph-based tutoring workflow.
    """

    def __init__(self):
        """Initialize logger and checkpointer."""
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkpointer = MemorySaver()
        self.app = None
        self.supervisor = None
        self.tutor = None
        self.evaluator = None
        self.retriever = None

    async def _initialize(self):
        """Build the unified LangGraph workflow graph."""
        # Initialize agents
        self.supervisor = await SuperviserAgent.get_instance()
        self.tutor = await TutorAgent.get_instance()
        self.evaluator = await EvaluatorAgent.get_instance()
        self.retriever = ContextRetriever.get_instance()

        # Build unified graph
        workflow = StateGraph(WorkflowState)

        # Add nodes
        workflow.add_node("supervisor", self.supervisor.call_llm)
        workflow.add_node("tutor", self.tutor.call_llm)
        workflow.add_node("evaluator", self.evaluator.call_llm)

        # Set entry point
        workflow.set_entry_point("supervisor")

        # Add conditional edges from supervisor
        workflow.add_conditional_edges(
            "supervisor",
            self.supervisor.router,
            {"tutor": "tutor", "evaluator": "evaluator", "end": END},
        )

        # Tutor always goes back to supervisor for next instruction
        workflow.add_edge("tutor", "supervisor")

        # Evaluator marks the end of the AI part and waits for HITL
        workflow.add_edge("evaluator", END)

        # Compile with interrupt and checkpointer
        self.app = workflow.compile(
            checkpointer=self.checkpointer, interrupt_after=["tutor", "evaluator"]
        )

    async def _create_question_record(
        self, db: AsyncSession, user_id: int, question_text: str
    ) -> Question:
        """Creates a new question record in the database."""
        new_question = Question(
            user_id=user_id,
            question_text=question_text,
            reference_answer="To be provided",
        )
        db.add(new_question)
        await db.commit()
        await db.refresh(new_question)
        return new_question

    async def _sync_initial_workflow_state(
        self, db: AsyncSession, question_id: int, state_values: Dict[str, Any]
    ):
        """Syncs the initial AI-generated state back to the database."""
        stmt = (
            update(Question)
            .where(Question.id == question_id)
            .values(
                rephrased_question=state_values.get("question"),
                reference_answer=state_values.get("reference_answer", "No reference answer."),
                ai_assistant_feedback=state_values.get("ai_assistant_feedback"),
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def ask_question(
        self,
        db: AsyncSession,
        user_id: int,
        question_text: str,
        namespace: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Initializes the workflow and creates a database record."""
        context = await self.retriever.retrieve_context(question_text, namespace)
        question = await self._create_question_record(db, user_id, question_text)

        initial_state = {
            "messages": [HumanMessage(content=question_text)],
            "context": context,
            "question": question_text,
            "user_id": user_id,
            "question_id": question.id,
            "student_answer": None,
            "reference_answer": None,
            "evaluation": None,
            "ai_assistant_feedback": None,
            "is_approved": None,
            "human_comment": None,
            "final_score": None,
            "next_node": None,
        }

        config = {"configurable": {"thread_id": str(question.id)}}

        async for checkpoint in self.app.astream(
            initial_state, config=config, stream_mode="values"
        ):
            self.logger.debug(
                "Workflow progress: %s",
                checkpoint.get('next_node', 'unknown')
            )

        final_state = await self.app.aget_state(config)
        state_values = final_state.values

        await self._sync_initial_workflow_state(db, question.id, state_values)
        return state_values

    async def _get_owned_question(
        self, db: AsyncSession, user_id: int, question_id: int
    ) -> Question:
        """Retrieves a question and verifies ownership."""
        query = select(Question).where(Question.id == question_id)
        result = await db.execute(query)
        question = result.scalar_one_or_none()

        if not question:
            raise ValueError("Question not found")
        if question.user_id != user_id:
            raise PermissionError("Unauthorized: You do not own this question session")
        return question

    async def _sync_evaluation_to_db(
        self, db: AsyncSession, question_id: int, state_values: Dict[str, Any]
    ):
        """Syncs AI evaluation results back to the database."""
        evaluation = state_values.get("evaluation", {})
        ai_score = None
        improvements = None

        if isinstance(evaluation, dict):
            ai_score = evaluation.get("score")
            feedback = (
                evaluation.get("feedback")
                or evaluation.get("raw_output")
                or str(evaluation)
            )
            imps = evaluation.get("improvements")
            if isinstance(imps, list):
                improvements = "; ".join(str(i) for i in imps)
            elif imps:
                improvements = str(imps)
        else:
            feedback = str(evaluation)

        stmt = (
            update(Question)
            .where(Question.id == question_id)
            .values(
                ai_score=ai_score,
                ai_assistant_feedback=feedback,
                improvements=improvements,
            )
        )
        await db.execute(stmt)
        await db.commit()

    async def submit_answer(
        self, db: AsyncSession, user_id: int, question_id: int, student_answer: str
    ) -> Dict[str, Any]:
        """Submits the student's answer and triggers evaluation."""
        await self._get_owned_question(db, user_id, question_id)
        config = {"configurable": {"thread_id": str(question_id)}}

        stmt = (
            update(Question)
            .where(Question.id == question_id)
            .values(student_answer=student_answer)
        )
        await db.execute(stmt)
        await db.commit()

        try:
            update_data = {
                "student_answer": student_answer,
                "messages": [HumanMessage(content=student_answer)]
            }
            await self.app.aupdate_state(config, update_data)
        except Exception as e:
            self.logger.error("Failed to update state for question %s: %s", question_id, e)
            raise ValueError(f"Could not find an active session for question {question_id}.") from e

        async for checkpoint in self.app.astream(None, config=config, stream_mode="values"):
            self.logger.debug("Workflow progress: %s", checkpoint.get('next_node', 'unknown'))

        final_state = await self.app.aget_state(config)
        await self._sync_evaluation_to_db(db, question_id, final_state.values)
        return final_state.values

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    async def submit_review(
        self,
        db: AsyncSession,
        question_id: int,
        is_approved: bool,
        human_comment: Optional[str] = None,
        final_score: Optional[int] = None,
        reviewer_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Handles human review and finalizes the assessment."""
        config = {"configurable": {"thread_id": str(question_id)}}

        stmt = (
            update(Question)
            .where(Question.id == question_id)
            .values(
                is_approved=is_approved,
                human_feedback=human_comment,
                final_score=final_score,
                approved_by=reviewer_id
            )
        )
        await db.execute(stmt)
        await db.commit()

        update_data = {
            "is_approved": is_approved,
            "human_comment": human_comment,
            "final_score": final_score,
            "approved_by": reviewer_id
        }
        await self.app.aupdate_state(config, update_data)

        async for _ in self.app.astream(None, config=config, stream_mode="values"):
            self.logger.debug("Workflow resumed after human review.")

        final_state = await self.app.aget_state(config)
        return final_state.values

    async def get_pending_reviews(self, db: AsyncSession) -> List[Question]:
        """Retrieves all questions that have not been approved yet."""
        query = select(Question).where(Question.is_approved.is_(False))
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_state(self, thread_id: str) -> Dict[str, Any]:
        """Gets the current state of a workflow."""
        config = {"configurable": {"thread_id": thread_id}}
        state = await self.app.aget_state(config)
        return state.values
