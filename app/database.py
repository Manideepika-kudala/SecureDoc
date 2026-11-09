import os

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker

from app.models.base import Base


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./securedoc.db")

# Render/Neon PostgreSQL URLs use psycopg 3.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+psycopg://", 1
    )
elif DATABASE_URL.startswith("postgresql://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgresql://", "postgresql+psycopg://", 1
    )

IS_SQLITE = DATABASE_URL.startswith("sqlite")

engine_options = {}
if IS_SQLITE:
    engine_options["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_options)


if IS_SQLITE:
    @event.listens_for(engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _configure_sqlite_audit_protection(connection):
    connection.execute(
        text("DROP TRIGGER IF EXISTS prevent_audit_log_update")
    )

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


def _configure_postgresql_audit_protection(connection):
    connection.execute(text("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_update_fn()
        RETURNS trigger AS $$
        BEGIN
            IF OLD.id IS DISTINCT FROM NEW.id
                OR OLD.action IS DISTINCT FROM NEW.action
                OR OLD.outcome IS DISTINCT FROM NEW.outcome
                OR OLD.details::text IS DISTINCT FROM NEW.details::text
                OR OLD.ip_address IS DISTINCT FROM NEW.ip_address
                OR OLD.created_at IS DISTINCT FROM NEW.created_at
                OR (
                    OLD.actor_user_id IS DISTINCT FROM NEW.actor_user_id
                    AND NEW.actor_user_id IS NOT NULL
                )
                OR (
                    OLD.document_id IS DISTINCT FROM NEW.document_id
                    AND NEW.document_id IS NOT NULL
                )
                OR (
                    OLD.actor_user_id IS NOT DISTINCT FROM NEW.actor_user_id
                    AND OLD.document_id IS NOT DISTINCT FROM NEW.document_id
                )
            THEN
                RAISE EXCEPTION 'Audit logs are append-only';
            END IF;

            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    connection.execute(text("""
        CREATE OR REPLACE FUNCTION prevent_audit_log_delete_fn()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION 'Audit logs are append-only';
        END;
        $$ LANGUAGE plpgsql;
    """))

    connection.execute(text("""
        DROP TRIGGER IF EXISTS prevent_audit_log_update
        ON audit_logs;
    """))

    connection.execute(text("""
        CREATE TRIGGER prevent_audit_log_update
        BEFORE UPDATE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_update_fn();
    """))

    connection.execute(text("""
        DROP TRIGGER IF EXISTS prevent_audit_log_delete
        ON audit_logs;
    """))

    connection.execute(text("""
        CREATE TRIGGER prevent_audit_log_delete
        BEFORE DELETE ON audit_logs
        FOR EACH ROW
        EXECUTE FUNCTION prevent_audit_log_delete_fn();
    """))


def create_tables():
    from app.models.user import User
    from app.models.document import Document
    from app.models.permission import DocumentPermission
    from app.models.audit import AuditLog
    from app.models.login_attempt import LoginAttempt

    Base.metadata.create_all(bind=engine)

    with engine.begin() as connection:
        if engine.dialect.name == "sqlite":
            user_columns = {
                row[1] for row in connection.execute(
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

            if "role" not in user_columns:
                connection.execute(text(
                    "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'owner'"
                ))

            connection.execute(text(
                "UPDATE users SET role = 'admin' WHERE is_admin = 1"
            ))

            document_columns = {
                row[1] for row in connection.execute(
                    text("PRAGMA table_info(documents)")
                ).fetchall()
            }

            if "category" not in document_columns:
                connection.execute(text(
                    "ALTER TABLE documents ADD COLUMN category VARCHAR(80) NOT NULL DEFAULT 'General'"
                ))

            _configure_sqlite_audit_protection(connection)

        elif engine.dialect.name == "postgresql":
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER NOT NULL DEFAULT 0"))
            connection.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN NOT NULL DEFAULT FALSE"))
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'owner'"
            ))
            connection.execute(text(
                "UPDATE users SET role = 'admin' WHERE is_admin = TRUE"
            ))
            connection.execute(text(
                "ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(80) NOT NULL DEFAULT 'General'"
            ))
            _configure_postgresql_audit_protection(connection)

        else:
            raise RuntimeError(
                f"Unsupported database dialect: {engine.dialect.name}"
            )
