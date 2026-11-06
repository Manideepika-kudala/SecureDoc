from datetime import timezone
from pathlib import Path
import shutil
import zipfile
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
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".ppt": "application/vnd.ms-powerpoint",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation"
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

        if extension in {".docx", ".pptx"}:
            try:
                with zipfile.ZipFile(file_path) as office_file:
                    entries = set(office_file.namelist())

                required_entries = {
                    "[Content_Types].xml",
                    "word/document.xml" if extension == ".docx"
                    else "ppt/presentation.xml"
                }

                if not required_entries.issubset(entries):
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid Office document structure"
                    )

            except zipfile.BadZipFile:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid Office document archive"
                )
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


@router.get("/{document_id}/edit")
def get_text_document_for_editing(
    document_id: int,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = get_authorized_document(
        document_id=document_id,
        user=user,
        db=db,
        required_level="editor",
        request=request
    )

    if Path(document.original_filename).suffix.lower() != ".txt":
        raise HTTPException(
            status_code=415,
            detail="Editing is currently supported only for TXT files"
        )

    file_path = (STORAGE_DIR / document.stored_filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found")

    if file_path.stat().st_size > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Text file exceeds the 5 MB edit limit")

    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=415, detail="File is not valid UTF-8 text")

    return {
        "document_id": document.id,
        "filename": document.original_filename,
        "content": content
    }



@router.put("/{document_id}/edit")
async def edit_text_document(
    document_id: int,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = get_authorized_document(
        document_id=document_id,
        user=user,
        db=db,
        required_level="editor",
        request=request
    )

    extension = Path(document.original_filename).suffix.lower()

    if extension != ".txt":
        raise HTTPException(
            status_code=415,
            detail="Editing is currently supported only for TXT files"
        )

    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(payload, dict) or not isinstance(payload.get("content"), str):
        raise HTTPException(
            status_code=400,
            detail="A text content field is required"
        )

    content = payload["content"]

    if "\x00" in content:
        raise HTTPException(status_code=400, detail="Null bytes are not allowed")

    content_bytes = content.encode("utf-8")

    if len(content_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Text file exceeds the 5 MB edit limit")

    file_path = (STORAGE_DIR / document.stored_filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found")

    temporary_path = file_path.with_name(
        f".{file_path.name}.{uuid4().hex}.tmp"
    )

    try:
        temporary_path.write_bytes(content_bytes)
        temporary_path.replace(file_path)

        document.file_size = len(content_bytes)

        record_audit_event(
            db=db,
            action="document_edit",
            outcome="success",
            actor_user_id=user.id,
            document_id=document.id,
            details={"filename": document.original_filename},
            ip_address=request.client.host if request.client else None
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        temporary_path.unlink(missing_ok=True)

    return {
        "message": "Document updated successfully",
        "document_id": document.id,
        "file_size": document.file_size
    }





@router.put("/{document_id}/replace")
async def replace_document_file(
    document_id: int,
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = get_authorized_document(
        document_id=document_id,
        user=user,
        db=db,
        required_level="editor",
        request=request
    )

    extension = Path(document.original_filename).suffix.lower()
    expected_type = ALLOWED_TYPES.get(extension)

    if not expected_type or file.content_type != expected_type:
        raise HTTPException(
            status_code=400,
            detail="Replacement must use the same supported file type"
        )

    header = await file.read(16)
    await file.seek(0)

    if not validate_file_signature(extension, header):
        raise HTTPException(
            status_code=400,
            detail="File content does not match the declared file type"
        )

    file_path = (STORAGE_DIR / document.stored_filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found")

    temporary_path = file_path.with_name(
        f".{file_path.name}.{uuid4().hex}.tmp"
    )
    backup_path = file_path.with_name(
        f".{file_path.name}.{uuid4().hex}.bak"
    )

    file_size = 0
    backup_created = False
    replacement_installed = False

    try:
        with temporary_path.open("xb") as destination:
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
            raise HTTPException(
                status_code=400,
                detail="Empty files are not allowed"
            )

        shutil.copy2(file_path, backup_path)
        backup_created = True

        temporary_path.replace(file_path)
        replacement_installed = True

        old_size = document.file_size
        document.file_size = file_size
        document.content_type = expected_type

        record_audit_event(
            db=db,
            action="document_replace",
            outcome="success",
            actor_user_id=user.id,
            document_id=document.id,
            details={
                "filename": document.original_filename,
                "old_size": old_size,
                "new_size": file_size
            },
            ip_address=request.client.host if request.client else None
        )

        db.commit()

        backup_path.unlink(missing_ok=True)

        return {
            "message": "Document replaced successfully",
            "document_id": document.id,
            "filename": document.original_filename,
            "file_size": file_size
        }

    except Exception:
        db.rollback()

        if replacement_installed and backup_created:
            backup_path.replace(file_path)
        raise

    finally:
        temporary_path.unlink(missing_ok=True)
        backup_path.unlink(missing_ok=True)
        await file.close()

@router.get("/{document_id}/preview")
def preview_document(
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

    preview_types = {
        ".pdf": "application/pdf",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".txt": "text/plain"
    }

    extension = Path(document.original_filename).suffix.lower()

    if extension not in preview_types:
        raise HTTPException(
            status_code=415,
            detail="Preview is not supported for this file type. Please download it."
        )

    file_path = (STORAGE_DIR / document.stored_filename).resolve()

    if file_path.parent != STORAGE_DIR.resolve() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Document file not found")

    record_audit_event(
        db=db,
        action="document_preview",
        outcome="success",
        actor_user_id=user.id,
        document_id=document.id,
        details={"filename": document.original_filename},
        ip_address=request.client.host if request.client else None
    )
    db.commit()

    return FileResponse(
        path=file_path,
        media_type=preview_types[extension],
        headers={
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff"
        }
    )


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
        filename=document.original_filename,
        headers={
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "private, no-store, max-age=0",
            "Pragma": "no-cache",
        }
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
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    document = db.get(Document, document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.owner_id != user.id:
        record_audit_event(
            db=db,
            action="permission_view",
            outcome="denied",
            actor_user_id=user.id,
            document_id=document_id,
            details={"reason": "not_document_owner"},
            ip_address=request.client.host if request.client else None
        )
        db.commit()
        raise HTTPException(
            status_code=403,
            detail="Only the owner can view sharing details"
        )

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
        record_audit_event(
            db=db,
            action="permission_grant",
            outcome="denied",
            actor_user_id=user.id,
            document_id=document_id,
            details={"reason": "not_document_owner"},
            ip_address=request.client.host if request.client else None
        )
        db.commit()
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
        record_audit_event(
            db=db,
            action="permission_revoke",
            outcome="denied",
            actor_user_id=user.id,
            document_id=document_id,
            details={"reason": "not_document_owner"},
            ip_address=request.client.host if request.client else None
        )
        db.commit()
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
    q: str | None = None,
    content_type: str | None = None,
    ownership: str = "all",
    date_from: str | None = None,
    date_to: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    from datetime import date

    if ownership not in {"all", "owned", "shared"}:
        raise HTTPException(status_code=400, detail="Invalid ownership filter")

    if sort_by not in {"filename", "created_at", "file_size"}:
        raise HTTPException(status_code=400, detail="Invalid sort field")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort order")

    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="Limit must be between 1 and 100")

    if offset < 0:
        raise HTTPException(status_code=400, detail="Offset cannot be negative")

    try:
        start_date = date.fromisoformat(date_from) if date_from else None
        end_date = date.fromisoformat(date_to) if date_to else None
    except ValueError:
        raise HTTPException(status_code=400, detail="Dates must use YYYY-MM-DD format")

    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="date_from cannot be after date_to")

    result = []

    if ownership in {"all", "owned"}:
        owned_documents = db.scalars(
            select(Document).where(Document.owner_id == user.id)
        ).all()

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
                "access_level": None,
                "created_at": document.created_at.isoformat() if document.created_at else None
            })

    if ownership in {"all", "shared"}:
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
                "access_level": permission.access_level,
                "created_at": document.created_at.isoformat() if document.created_at else None
            })

    if q:
        search_term = q.strip().casefold()
        result = [
            item for item in result
            if search_term in item["filename"].casefold()
            or search_term in item["content_type"].casefold()
        ]

    if content_type:
        selected_type = content_type.strip().casefold()
        result = [
            item for item in result
            if selected_type in item["content_type"].casefold()
        ]

    if start_date:
        result = [
            item for item in result
            if item["created_at"]
            and date.fromisoformat(item["created_at"][:10]) >= start_date
        ]

    if end_date:
        result = [
            item for item in result
            if item["created_at"]
            and date.fromisoformat(item["created_at"][:10]) <= end_date
        ]

    sort_key = {
        "filename": lambda item: item["filename"].casefold(),
        "created_at": lambda item: item["created_at"] or "",
        "file_size": lambda item: item["file_size"],
    }[sort_by]

    result.sort(key=sort_key, reverse=(sort_order == "desc"))

    return result[offset:offset + limit]


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


    if extension == ".pptx":
        return header.startswith(b"PK\x03\x04")

    if extension == ".ppt":
        return header.startswith(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1")
    validator = signatures.get(extension)
    return validator(header) if validator else False

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    request: Request,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if document.owner_id != user.id:
        record_audit_event(
            db,
            action="document_delete",
            outcome="denied",
            actor_user_id=user.id,
            document_id=document.id,
            details={"reason": "not_owner"},
            ip_address=request.client.host if request.client else None,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the document owner can delete this document",
        )

    storage_root = STORAGE_DIR.resolve()
    file_path = (storage_root / document.stored_filename).resolve()

    if file_path.parent != storage_root:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document storage path",
        )

    quarantine_path = None

    try:
        if file_path.is_file():
            quarantine_path = file_path.with_name(
                f".{file_path.name}.deleting-{uuid4().hex}"
            )
            file_path.replace(quarantine_path)

        record_audit_event(
            db,
            action="document_delete",
            outcome="success",
            actor_user_id=user.id,
            document_id=document.id,
            details={
                "document_id": document.id,
                "filename": document.original_filename,
                "storage_file_missing": quarantine_path is None,
            },
            ip_address=request.client.host if request.client else None,
        )

        db.delete(document)
        db.commit()

    except Exception:
        db.rollback()

        if quarantine_path is not None and quarantine_path.exists():
            quarantine_path.replace(file_path)

        raise

    if quarantine_path is not None and quarantine_path.exists():
        quarantine_path.unlink()

    return {"message": "Document deleted successfully"}




