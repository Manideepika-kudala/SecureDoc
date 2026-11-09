# SecureDoc — Secure Document Management System

**Overall Project Status: 100% COMPLETED**

## 1. Project Overview

SecureDoc is a secure document management and sharing application built with FastAPI. It provides authentication, role-based access control, document management, controlled sharing, audit logging, and administrative monitoring.

## 2. Core Features

### Authentication
- User registration, login and logout.
- Argon2 password hashing.
- Session-based authentication.
- Session version invalidation.
- Login rate limiting.
- Secure session cookies.

### User Roles and Authorization
- Admin, Owner and Viewer account roles.
- Document-level Viewer and Editor permissions.
- Server-side authorization.
- Document ownership validation.
- Permission granting, updating and revocation.
- Read-only restrictions for Viewer accounts.

### Document Management
- Secure upload and download.
- Document replacement and editing.
- Supported document previews.
- Document search and filtering.
- File type, MIME type and signature validation.
- Upload size and empty-file validation.
- Filename sanitization.
- DOCX/PPTX archive validation.
- Path traversal protection.
- Private document storage.

### Sharing
- Owner-controlled document sharing.
- Viewer and Editor permissions.
- Permission updates and revocation.
- Unauthorized access prevention.

### Audit and Administration
- Audit logging for security actions.
- Append-only audit protections.
- Administrative activity monitoring.
- Admin overview endpoint.
- Activity filtering and pagination.
- Audit history retention protections.

### Application Security
- CSRF protection.
- Secure HTTP response headers.
- Session security.
- Rate limiting.
- Server-side authorization.
- Secure file handling.

## 3. Technology Stack

| Component | Technology |
|---|---|
| Language | Python 3.13 |
| Backend | FastAPI |
| Server | Uvicorn |
| ORM | SQLAlchemy |
| Databases | SQLite, PostgreSQL |
| PostgreSQL Driver | Psycopg 3 |
| Validation | Pydantic |
| Templates | Jinja2 |
| Password Security | Argon2 |
| Testing | Pytest, HTTPX |
| Deployment | Render |
| Version Control | Git, GitHub |

## 4. Account Roles

| Role | Capabilities |
|---|---|
| Admin | Administrative dashboard and activity monitoring |
| Owner | Manage, upload, share, replace and delete owned documents |
| Viewer | Read documents explicitly shared with the account |

Account roles and document permissions are evaluated separately.

## 5. Local Installation

Create a virtual environment:

    python -m venv venv

Activate it:

    .\venv\Scripts\Activate.ps1

Install dependencies:

    python -m pip install -r requirements.txt

Configure the application secret:

    $env:SECUREDOC_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(32))")

Start the application:

    python -m uvicorn app.main:app --reload

Open:

    http://127.0.0.1:8000

## 6. Environment Variables

| Variable | Purpose |
|---|---|
| SECUREDOC_SECRET_KEY | Application session secret |
| SECUREDOC_HTTPS_ONLY | HTTPS-only cookie behavior |
| DATABASE_URL | Database connection string |

SQLite is the default local database. PostgreSQL can be configured through DATABASE_URL.

Never commit production secrets or database passwords to Git.

## 7. Database

- SQLite support for local development.
- PostgreSQL support for deployment.
- SQLAlchemy database operations.
- Application startup table initialization.
- Audit protections using database triggers for supported engines.

## 8. Testing

Run the test suite:

    python -m pytest -q

Latest recorded local results:

- Full regression suite: 81 passed.
- Audit tests: 17 passed.
- Python compilation check: successful.

These are previously recorded results, not a new test execution during this documentation update.

## 9. Deployment

Deployment platform: Render.

Recorded service:
- Service name: securedoc-live
- Application URL: https://securedoc-live.onrender.com
- Git branch: main
- Recorded deployment commit: f13fd6c

The deployment logs previously showed successful application startup and an HTTP 200 response for the home page.

### Render Free Plan Limitations

- Services may spin down after inactivity.
- Local filesystem storage is ephemeral.
- Locally stored documents may not survive restarts or redeployments.
- Free PostgreSQL databases have limited lifetime and backup guarantees.
- PPT/PPTX previews depend on LibreOffice availability.

Persistent storage and an appropriate production database plan are recommended for confidential documents.

## 10. Security Considerations

SecureDoc implements authentication, server-side authorization, ownership validation, permission revocation, CSRF protection, secure sessions, rate limiting, file validation, path traversal protection and audit logging.

Security controls should be maintained when adding new functionality.

## 11. Project Documentation

| File | Purpose |
|---|---|
| README.md | Project overview and setup |
| DAILY_PROGRESS.md | Development progress |
| IMPLEMENTATION_PLAN.md | Implementation plan |
| API.md | API documentation |
| PROBLEM_STATEMENT.md | Problem statement |
| THREATS.md | Threat analysis |
| PROMPTS.md | Development prompts |

## 12. Final Project Status

The project completion status is recorded as requested by the project owner.

- Core application implementation.
- Authentication and account management.
- Admin, Owner and Viewer roles.
- Document management and sharing.
- Server-side authorization.
- Audit logging and administration.
- Application security controls.
- SQLite and PostgreSQL support.
- Automated regression tests.
- Project documentation.
- Render deployment configuration.
- Git and GitHub management.

**Overall Project Status: 100% COMPLETED**

## 13. Conclusion

SecureDoc combines secure backend development, document management, role-based authorization, controlled sharing, audit logging, automated testing and cloud deployment configuration.

**SecureDoc — Project Completed.**
