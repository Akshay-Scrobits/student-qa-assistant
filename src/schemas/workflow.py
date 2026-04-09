"""
Schemas for the AI assessment workflow state.
"""
import operator
from typing import TypedDict, Annotated, List, Optional

from langchain_core.messages import BaseMessage


class WorkflowState(TypedDict):
    """State for the AI assessment workflow."""

    messages: Annotated[List[BaseMessage], operator.add]
    context: str
    question: str
    user_id: Optional[int]
    question_id: Optional[int]
    student_answer: Optional[str]
    reference_answer: Optional[str]
    evaluation: Optional[dict]
    ai_assistant_feedback: Optional[str]
    is_approved: Optional[bool]
    human_comment: Optional[str]
    final_score: Optional[int]
    approved_by: Optional[int]
    next_node: Optional[str]
