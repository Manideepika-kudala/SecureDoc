from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit_event(
    db: Session,
    action: str,
    outcome: str,
    actor_user_id: int | None = None,
    document_id: int | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    if outcome not in {"success", "denied"}:
        raise ValueError("Invalid audit outcome")

    event = AuditLog(
        actor_user_id=actor_user_id,
        document_id=document_id,
        action=action,
        outcome=outcome,
        details=details or {},
        ip_address=ip_address,
    )

    db.add(event)
    db.flush()

    return event
