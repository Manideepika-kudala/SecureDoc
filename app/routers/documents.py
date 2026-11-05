from datetime import timezone
from pathlib import Path
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
    status
)
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.document import PermissionGrant
from app.services.authorization import get_current_active_user
from app.services.audit import record_audit_event


router = APIRouter(prefix="/documents", tags=["Documents"])

STORAGE_DIR = Path(__file__).resolve().parents[2] / "storage" / "uploads"

MAX_FILE_SIZE = 200 * 1024 * 1024

ALLOWED_TYPES = {
    ".pdf": "application/pdf",
    ".txt": "text/plain",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
}


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    original_filename = Path(file.filename.replace(chr(92), "/")).name

    if len(original_filename) > 255:
        raise HTTPException(status_code=400, detail="Filename is too long")

    extension = Path(original_filename).suffix.lower()
    expected_type = ALLOWED_TYPES.get(extension)

    if not expected_type or file.content_type != expected_type:
        raise HTTPException(status_code=400, detail="File type is not allowed")

    header = await file.read(16)
    await file.seek(0)

    if not validate_file_signature(extension, header):
        raise HTTPException(
            status_code=400,
            detail="File content does not match the declared file type"
        )

    stored_filename = f"{uuid4().hex}{extension}"

    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = (STORAGE_DIR / stored_filename).resolve()

    file_size = 0

    try:
        with file_path.open("xb") as destination:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > MAX_FILE_SIZE:
                    raise HTTPException(
                        status_code=413,
                        detail="Maximum file size is 200 MB"
                    )

                destination.write(chunk)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty files are not allowed")

        document = Document(
            owner_id=user.id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            content_type=expected_type,
            file_size=file_size
        )

        db.add(document)
        db.flush()

        record_audit_event(
            db=db,
            action="document_upload",
            outcome="success",
            actor_user_id=user.id,
            document_id=document.id,
            details={
                "filename": original_filename,
                "file_size": file_size
            },
            ip_address=request.client.host if request.client else None
        )

        db.commit()
        db.refresh(document)

        return {
            "message": "Document uploaded successfully",
            "document_id": document.id,
            "filename": document.original_filename,
            "file_size": document.file_size
        }

    except Exception:
        db.rollback()
        file_path.unlink(missing_ok=True)
        raise

    finally:
        await file.close()

from fastapi.responses import FileResponse

from app.models.permission import DocumentPermission
from app.services.authorization import get_authorized_document


@router.get("/{document_id}/download")
def download_document(
    document_id: int,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = get_authorized_document(
        document_id=document_id,
        user=user,
        db=db,
        required_level="viewer",
        request=request
    )

    file_path = (STORAGE_DIR / document.stored_filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="Document file not found"
        )

    record_audit_event(
        db=db,
        action="document_download",
        outcome="success",
        actor_user_id=user.id,
        document_id=document.id,
        details={"filename": document.original_filename},
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=document.original_filename
    )




@router.get("/{document_id}/users/search")
def search_share_users(
    document_id: int,
    q: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can search users")

    query = q.strip()

    if len(query) < 2:
        raise HTTPException(status_code=400, detail="Enter at least 2 characters")

    users = db.scalars(
        select(User)
        .where(
            User.is_active.is_(True),
            User.id != user.id,
            or_(
                User.username.ilike(f"%{query}%"),
                User.email.ilike(f"%{query}%")
            )
        )
        .order_by(User.username)
        .limit(10)
    ).all()

    return [
        {
            "user_id": target.id,
            "username": target.username,
            "email": target.email
        }
        for target in users
    ]


@router.get("/{document_id}/permissions")
def list_document_permissions(
    document_id: int,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can view sharing details")

    permissions = db.execute(
        select(DocumentPermission, User)
        .join(User, DocumentPermission.user_id == User.id)
        .where(DocumentPermission.document_id == document_id)
        .order_by(DocumentPermission.granted_at.desc())
    ).all()

    return [
        {
            "user_id": target.id,
            "username": target.username,
            "email": target.email,
            "access_level": permission.access_level,
            "granted_at": permission.granted_at.isoformat()
        }
        for permission, target in permissions
    ]

@router.post("/{document_id}/permissions")
def grant_document_permission(
    document_id: int,
    permission_data: PermissionGrant,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the document owner can grant permissions"
        )

    target_user = db.get(User, permission_data.user_id)

    if not target_user or not target_user.is_active:
        raise HTTPException(status_code=404, detail="Active target user not found")

    if target_user.id == user.id:
        raise HTTPException(status_code=400, detail="You already own this document")

    permission = db.scalar(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == target_user.id
        )
    )

    if permission:
        permission.access_level = permission_data.access_level
        audit_action = "permission_update"
    else:
        permission = DocumentPermission(
            document_id=document_id,
            user_id=target_user.id,
            granted_by=user.id,
            access_level=permission_data.access_level
        )
        db.add(permission)
        audit_action = "permission_grant"

    record_audit_event(
        db=db,
        action=audit_action,
        outcome="success",
        actor_user_id=user.id,
        document_id=document_id,
        details={
            "target_user_id": target_user.id,
            "access_level": permission_data.access_level
        },
        ip_address=request.client.host if request.client else None
    )

    db.commit()
    db.refresh(permission)

    return {
        "message": "Document permission granted successfully",
        "document_id": permission.document_id,
        "user_id": permission.user_id,
        "access_level": permission.access_level,
        "granted_by": permission.granted_by
    }

@router.delete("/{document_id}/permissions/{target_user_id}")
def revoke_document_permission(
    document_id: int,
    target_user_id: int,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        raise HTTPException(
            status_code=403,
            detail="Only the document owner can revoke permissions"
        )

    permission = db.scalar(
        select(DocumentPermission).where(
            DocumentPermission.document_id == document_id,
            DocumentPermission.user_id == target_user_id
        )
    )

    if not permission:
        raise HTTPException(status_code=404, detail="Permission not found")

    db.delete(permission)

    record_audit_event(
        db=db,
        action="permission_revoke",
        outcome="success",
        actor_user_id=user.id,
        document_id=document_id,
        details={"target_user_id": target_user_id},
        ip_address=request.client.host if request.client else None
    )

    db.commit()

    return {
        "message": "Document permission revoked successfully",
        "document_id": document_id,
        "user_id": target_user_id
    }

@router.get("/")
def list_documents(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    owned_documents = db.scalars(
        select(Document).where(Document.owner_id == user.id)
    ).all()

    result = []

    for document in owned_documents:
        result.append({
            "id": document.id,
            "filename": document.original_filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "owner_id": document.owner_id,
            "is_owner": True,
            "shared_by_username": None,
            "shared_by_email": None,
            "shared_at": None,
            "access_level": None
        })

    shared_permissions = db.scalars(
        select(DocumentPermission).where(
            DocumentPermission.user_id == user.id
        )
    ).all()

    for permission in shared_permissions:
        document = db.get(Document, permission.document_id)

        if not document:
            continue

        shared_by = db.get(User, permission.granted_by)

        shared_at = permission.granted_at

        if shared_at and shared_at.tzinfo is None:
            shared_at = shared_at.replace(tzinfo=timezone.utc)

        result.append({
            "id": document.id,
            "filename": document.original_filename,
            "content_type": document.content_type,
            "file_size": document.file_size,
            "owner_id": document.owner_id,
            "is_owner": False,
            "shared_by_username": shared_by.username if shared_by else "Unknown",
            "shared_by_email": shared_by.email if shared_by else None,
            "shared_at": shared_at.isoformat() if shared_at else None,
            "access_level": permission.access_level
        })

    return result


def validate_file_signature(extension: str, header: bytes) -> bool:
    signatures = {
        ".pdf": lambda data: data.startswith(b"%PDF-"),
        ".png": lambda data: data.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": lambda data: data.startswith(b"\xff\xd8\xff"),
        ".jpeg": lambda data: data.startswith(b"\xff\xd8\xff"),
    }

    if extension == ".txt":
        return b"\x00" not in header

    if extension == ".docx":
        return header.startswith(b"PK\x03\x04")

    validator = signatures.get(extension)
    return validator(header) if validator else False



