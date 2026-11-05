from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base

DATABASE_URL = "sqlite:///./securedoc.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

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

    Base.metadata.create_all(bind=engine)

    from sqlalchemy import text

    with engine.begin() as connection:
        user_columns = {
            row[1]
            for row in connection.execute(
                text("PRAGMA table_info(users)")
            ).fetchall()
        }

        if "is_admin" not in user_columns:
            connection.execute(text("""
                ALTER TABLE users
                ADD COLUMN is_admin BOOLEAN NOT NULL DEFAULT 0
            """))

        connection.execute(text("""
            CREATE TRIGGER IF NOT EXISTS prevent_audit_log_update
            BEFORE UPDATE ON audit_logs
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
