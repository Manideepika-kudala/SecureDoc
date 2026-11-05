from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models.document import Document
from app.models.permission import DocumentPermission
from app.models.user import User
from app.services.audit import record_audit_event


def get_current_active_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    user_id = request.session.get("user_id")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    user = db.scalar(
        select(User).where(User.id == user_id)
    )

    if not user or not user.is_active:
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive user session"
        )

    return user



def get_current_admin_user(
    user: User = Depends(get_current_active_user)
) -> User:
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )

    return user


def _record_denied_access(
    user: User,
    document_id: int,
    reason: str,
    required_level: str,
    request: Request | None = None,
) -> None:
    audit_db = SessionLocal()

    try:
        record_audit_event(
            db=audit_db,
            action="document_access",
            outcome="denied",
            actor_user_id=user.id,
            document_id=document_id,
            details={
                "reason": reason,
                "required_level": required_level
            },
            ip_address=(
                request.client.host
                if request and request.client
                else None
            )
        )
        audit_db.commit()
    except Exception:
        audit_db.rollback()
    finally:
        audit_db.close()


def get_authorized_document(
    document_id: int,
    user: User,
    db: Session,
    required_level: str = "viewer",
    request: Request | None = None,
) -> Document:
    if required_level not in {"viewer", "editor"}:
        raise ValueError("Invalid required permission level")

    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    if document.owner_id == user.id:
        return document

    permission = db.scalar(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == user.id
        )
    )

    if not permission:
        _record_denied_access(
            user=user,
            document_id=document_id,
            reason="no_permission",
            required_level=required_level,
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this document"
        )

    allowed = (
        permission.access_level == "editor"
        or (
            permission.access_level == "viewer"
            and required_level == "viewer"
        )
    )

    if not allowed:
        _record_denied_access(
            user=user,
            document_id=document_id,
            reason="insufficient_permission",
            required_level=required_level,
            request=request
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient document permissions"
        )

    return document
