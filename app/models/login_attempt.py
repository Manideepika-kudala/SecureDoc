from datetime import datetime, timezone

from sqlalchemy import DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    __table_args__ = (
        Index("ix_login_attempts_blocked_until", "blocked_until"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    ip_address: Mapped[str] = mapped_column(
        String(45),
        unique=True,
        nullable=False
    )

    failed_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    window_started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False
    )

    blocked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
