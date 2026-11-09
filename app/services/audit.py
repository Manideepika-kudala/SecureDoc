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
    if not isinstance(action, str) or not action.strip():
        raise ValueError("Audit action must be a non-empty string")

    if len(action) > 50:
        raise ValueError("Audit action cannot exceed 50 characters")

    if not isinstance(outcome, str) or outcome not in {"success", "denied"}:
        raise ValueError("Invalid audit outcome")

    if details is not None and not isinstance(details, dict):
        raise ValueError("Audit details must be a dictionary")

    if ip_address is not None:
        if not isinstance(ip_address, str):
            raise ValueError("Audit IP address must be a string")

        if len(ip_address) > 45:
            raise ValueError("Audit IP address cannot exceed 45 characters")

    event = AuditLog(
        actor_user_id=actor_user_id,
        document_id=document_id,
        action=action,
        outcome=outcome,
        details=details if details is not None else {},
        ip_address=ip_address,
    )

    db.add(event)
    db.flush()

    return event

