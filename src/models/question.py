"""
Question model — stores the full lifecycle of a tutoring session.

Fields are populated progressively across three HTTP calls:
  /ask    → question_text, user_id, reference_answer
  /answer → student_answer, ai_score, confidence, ai_assistant_feedback, improvements
  /review → is_approved, approved_by, final_score, human_feedback
"""

from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Index, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base


# pylint: disable=too-few-public-methods
class Question(Base):
    """
    SQLAlchemy model representing a tutoring session question and its lifecycle.
    """
    __tablename__ = "questions"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    rephrased_question: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    reference_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    student_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ai_assistant_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    improvements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    approved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    final_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    human_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"Question(id={self.id}, user_id={self.user_id})"

    __table_args__ = (
        Index("idx_question_user_id", "user_id"),
        Index("idx_question_created_at", "created_at"),
    )
