"""
Base database model module.
Defines the common base class for all SQLAlchemy models with shared columns.
"""

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# pylint: disable=too-few-public-methods
class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy models.
    Includes default ID and timestamp columns.
    """

    id: Mapped[int] = mapped_column(primary_key=True)
    # pylint: disable=not-callable
    created_at: Mapped[datetime] = mapped_column(default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now()
    )
