from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models.login_attempt import LoginAttempt


MAX_FAILED_ATTEMPTS = 5
ATTEMPT_WINDOW_MINUTES = 15
BLOCK_DURATION_MINUTES = 15


def _utc_now():
    return datetime.now(timezone.utc)


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def is_ip_blocked(db: Session, ip_address: str):
    attempt = db.query(LoginAttempt).filter_by(
        ip_address=ip_address
    ).first()

    if not attempt:
        return None

    now = _utc_now()

    if attempt.blocked_until:
        blocked_until = _as_utc(attempt.blocked_until)

        if blocked_until > now:
            return blocked_until

        attempt.failed_attempts = 0
        attempt.blocked_until = None
        attempt.window_started_at = now
        db.commit()
        return None

    window_started_at = _as_utc(attempt.window_started_at)

    if now - window_started_at >= timedelta(
        minutes=ATTEMPT_WINDOW_MINUTES
    ):
        attempt.failed_attempts = 0
        attempt.window_started_at = now
        db.commit()

    return None


def record_failed_login(db: Session, ip_address: str):
    now = _utc_now()

    attempt = db.query(LoginAttempt).filter_by(
        ip_address=ip_address
    ).first()

    if not attempt:
        attempt = LoginAttempt(
            ip_address=ip_address,
            failed_attempts=1,
            window_started_at=now
        )
        db.add(attempt)
    else:
        window_started_at = _as_utc(attempt.window_started_at)

        if now - window_started_at >= timedelta(
            minutes=ATTEMPT_WINDOW_MINUTES
        ):
            attempt.failed_attempts = 0
            attempt.window_started_at = now

        attempt.failed_attempts += 1

    if attempt.failed_attempts >= MAX_FAILED_ATTEMPTS:
        attempt.blocked_until = now + timedelta(
            minutes=BLOCK_DURATION_MINUTES
        )

    db.commit()


def reset_login_attempts(db: Session, ip_address: str):
    attempt = db.query(LoginAttempt).filter_by(
        ip_address=ip_address
    ).first()

    if attempt:
        db.delete(attempt)
        db.commit()
