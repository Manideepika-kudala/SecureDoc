from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.audit import AuditLog
from app.models.document import Document
from app.models.user import User
from app.services.authorization import get_current_admin_user


router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/activity")
def get_admin_activity(
    outcome: Literal["success", "denied"] | None = None,
    action: str | None = Query(default=None, max_length=50),
    actor_user_id: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    filters = []

    if outcome is not None:
        filters.append(AuditLog.outcome == outcome)

    if action is not None:
        filters.append(AuditLog.action == action)

    if actor_user_id is not None:
        filters.append(AuditLog.actor_user_id == actor_user_id)

    total = db.scalar(
        select(func.count()).select_from(AuditLog).where(*filters)
    )

    events = db.scalars(
        select(AuditLog)
        .where(*filters)
        .order_by(desc(AuditLog.created_at), desc(AuditLog.id))
        .offset(offset)
        .limit(limit)
    ).all()

    return {
        "total": total or 0,
        "limit": limit,
        "offset": offset,
        "items": [
            {
                "id": event.id,
                "actor_user_id": event.actor_user_id,
                "document_id": event.document_id,
                "action": event.action,
                "outcome": event.outcome,
                "details": event.details,
                "ip_address": event.ip_address,
                "created_at": event.created_at,
            }
            for event in events
        ],
    }


@router.get("/overview")
def get_admin_overview(
    admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    total_users = db.scalar(
        select(func.count()).select_from(User)
    ) or 0

    total_documents = db.scalar(
        select(func.count()).select_from(Document)
    ) or 0

    total_events = db.scalar(
        select(func.count()).select_from(AuditLog)
    ) or 0

    successful_events = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.outcome == "success")
    ) or 0

    denied_events = db.scalar(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.outcome == "denied")
    ) or 0

    return {
        "total_users": total_users,
        "total_documents": total_documents,
        "total_events": total_events,
        "successful_events": successful_events,
        "denied_events": denied_events,
    }
