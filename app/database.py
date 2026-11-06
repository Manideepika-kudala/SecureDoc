from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

DATABASE_URL = "sqlite:///./securedoc.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    from app.models.user import User
    from app.models.document import Document
    from app.models.permission import DocumentPermission
    from app.models.audit import AuditLog
    from app.models.login_attempt import LoginAttempt

    Base.metadata.create_all(bind=engine)

    from sqlalchemy import text

    with engine.begin() as connection:
        user_columns = {
            row[1]
            for row in connection.execute(
                text("PRAGMA table_info(users)")
            ).fetchall()
        }

        if "session_version" not in user_columns:
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN session_version INTEGER NOT NULL DEFAULT 0
            """))

        if "is_admin" not in user_columns:
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0
            """))

        connection.execute(text(
            "DROP TRIGGER IF EXISTS prevent_audit_log_update"
        ))

        connection.execute(text("""
            CREATE TRIGGER prevent_audit_log_update
            BEFORE UPDATE ON audit_logs
            WHEN NOT (
                OLD.id IS NEW.id
                AND OLD.action IS NEW.action
                AND OLD.outcome IS NEW.outcome
                AND OLD.details IS NEW.details
                AND OLD.ip_address IS NEW.ip_address
                AND OLD.created_at IS NEW.created_at
                AND (
                    OLD.actor_user_id IS NEW.actor_user_id
                    OR NEW.actor_user_id IS NULL
                )
                AND (
                    OLD.document_id IS NEW.document_id
                    OR NEW.document_id IS NULL
                )
                AND (
                    OLD.actor_user_id IS NOT NEW.actor_user_id
                    OR OLD.document_id IS NOT NEW.document_id
                )
            )
            BEGIN
                SELECT RAISE(ABORT, 'Audit logs are append-only');
            END;
        """))

        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_audit_log_delete
            BEFORE DELETE ON audit_logs
            BEGIN
                SELECT RAISE(ABORT, 'Audit logs are append-only');
            END;
        """))
