from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin, UserRegister, UserResponse
from app.security import hash_password, verify_password
from app.services.audit import record_audit_event
from app.services.authorization import get_current_active_user
from app.services.login_rate_limit import (
    is_ip_blocked,
    record_failed_login,
    reset_login_attempts,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def save_auth_audit(
    db: Session,
    action: str,
    outcome: str,
    request: Request,
    actor_user_id: int | None = None,
    details: dict | None = None,
):
    record_audit_event(
        db=db,
        action=action,
        outcome=outcome,
        actor_user_id=actor_user_id,
        details=details or {},
        ip_address=get_client_ip(request),
    )
    db.commit()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def register_user(
    request: Request,
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    existing_user = db.scalar(
        select(User).where(
            (User.username == user_data.username)
            | (User.email == user_data.email)
        )
    )

    if existing_user:
        save_auth_audit(
            db=db,
            action="auth_register",
            outcome="denied",
            request=request,
            details={"reason": "username_or_email_already_registered"},
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already registered"
        )

    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    save_auth_audit(
        db=db,
        action="auth_register",
        outcome="success",
        request=request,
        actor_user_id=new_user.id,
    )

    return new_user


@router.post("/login")
def login_user(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db)
):
    ip_address = get_client_ip(request)
    blocked_until = is_ip_blocked(db, ip_address)

    if blocked_until:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        retry_after = max(1, int((blocked_until - now).total_seconds()))

        save_auth_audit(
            db=db,
            action="auth_login",
            outcome="denied",
            request=request,
            details={"reason": "ip_temporarily_blocked"},
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(retry_after)}
        )

    user = db.scalar(
        select(User).where(User.email == user_data.email)
    )

    if not user or not verify_password(
        user_data.password,
        user.password_hash
    ):
        record_failed_login(db, ip_address)

        save_auth_audit(
            db=db,
            action="auth_login",
            outcome="denied",
            request=request,
            actor_user_id=user.id if user else None,
            details={"reason": "invalid_credentials"},
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        save_auth_audit(
            db=db,
            action="auth_login",
            outcome="denied",
            request=request,
            actor_user_id=user.id,
            details={"reason": "inactive_account"},
        )

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    reset_login_attempts(db, ip_address)

    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["session_version"] = user.session_version

    save_auth_audit(
        db=db,
        action="auth_login",
        outcome="success",
        request=request,
        actor_user_id=user.id,
    )

    return {
        "message": "Login successful",
        "username": user.username
    }


@router.get("/me")
def get_current_user(
    user: User = Depends(get_current_active_user)
):
    return {
        "user_id": user.id,
        "username": user.username
    }


@router.post("/logout")
def logout_user(
    request: Request,
    db: Session = Depends(get_db)
):
    session_user_id = request.session.get("user_id")
    user = db.get(User, session_user_id) if session_user_id else None

    save_auth_audit(
        db=db,
        action="auth_logout",
        outcome="success",
        request=request,
        actor_user_id=user.id if user else None,
    )

    request.session.clear()

    return {"message": "Logout successful"}
