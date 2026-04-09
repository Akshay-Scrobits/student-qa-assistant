"""
Workflow router module for coordinating the tutoring and review process.
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from db.session import DBDep
from services.workflow import WorkflowService
from routers.deps import UserDep, role_required

router = APIRouter(prefix="/workflow", tags=["Workflow"])


class AskRequest(BaseModel):
    """Request model for asking a initial question."""
    question: str
    namespace: Optional[str] = None


class AnswerRequest(BaseModel):
    """Request model for submitting an answer."""
    question_id: int
    student_answer: str


class ReviewRequest(BaseModel):
    """Request model for human review of an answer."""
    question_id: int
    is_approved: bool
    final_score: int
    human_comment: Optional[str] = None


class QuestionResponse(BaseModel):
    """Response model for question details."""
    id: int
    question_id: Optional[int] = None
    user_id: int
    question_text: str
    rephrased_question: Optional[str] = None
    reference_answer: Optional[str] = None
    student_answer: Optional[str] = None
    ai_score: Optional[int] = None
    ai_assistant_feedback: Optional[str] = None
    improvements: Optional[str] = None
    is_approved: bool
    final_score: Optional[int] = None
    human_feedback: Optional[str] = None
    approved_by: Optional[int] = None
    created_at: Optional[datetime] = None

    # pylint: disable=too-few-public-methods
    class Config:
        """Pydantic configuration."""
        from_attributes = True


@router.post("/ask", dependencies=[Depends(role_required(["STUDENT"]))])
async def ask(request: AskRequest, db: DBDep, user: UserDep):
    """
    Initializes the tutoring session with a question.
    Session is bound to the current user.
    Context is automatically retrieved from the knowledge base (RAG).
    """
    service = await WorkflowService.get_instance()
    try:
        state = await service.ask_question(
            db,
            user.id,
            request.question,
            request.namespace
        )
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/answer", dependencies=[Depends(role_required(["STUDENT"]))])
async def answer(request: AnswerRequest, db: DBDep, user: UserDep):
    """
    Submits the student's answer and triggers AI evaluation.
    Pauses for human review.
    """
    service = await WorkflowService.get_instance()
    try:
        state = await service.submit_answer(
            db,
            user.id,
            request.question_id,
            request.student_answer
        )
        # Remove ai_assistant_feedback from the response as requested
        if "ai_assistant_feedback" in state:
            state.pop("ai_assistant_feedback")
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/pending", dependencies=[Depends(role_required(["REVIEWER"]))])
async def get_pending(db: DBDep, _user: UserDep):
    """
    Lists all questions that are pending human approval.
    """
    service = await WorkflowService.get_instance()
    try:
        pending = await service.get_pending_reviews(db)
        results = []
        for q in pending:
            data = QuestionResponse.model_validate(q)
            data.question_id = q.id  # Set the question_id field for cross-API consistency
            results.append(data)
        return {"pending": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/review", dependencies=[Depends(role_required(["REVIEWER"]))])
async def review(request: ReviewRequest, db: DBDep, user: UserDep):
    """
    Handles human review of the AI's evaluation.
    Finalizes the workflow with a score and comment.
    """
    service = await WorkflowService.get_instance()
    try:
        state = await service.submit_review(
            db,
            request.question_id,
            request.is_approved,
            request.human_comment,
            request.final_score,
            user.id
        )
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/state/{question_id}")
async def get_state(question_id: int, _user: UserDep):
    """
    Retrieves the current state of a workflow by its question ID.
    """
    service = await WorkflowService.get_instance()
    try:
        # thread_id is mapped to question_id internally
        thread_id = str(question_id)
        state = await service.get_state(thread_id)
        return {"state": state}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
