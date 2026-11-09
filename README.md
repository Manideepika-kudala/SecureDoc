# SecureDoc

SecureDoc is a secure document management and sharing application built with FastAPI.

## Features
- User registration and authentication
- Secure document upload and download
- Document-level VIEWER and EDITOR permissions
- Permission granting and revocation
- Secure file replacement
- Preview for supported file formats
- Document search and filtering
- Admin dashboard
- CSRF protection
- Argon2 password hashing
- Append-only audit logging

## User Roles
- Admin
- Owner
- Viewer

Document-level editor permissions are separate from account roles.

## Technology Stack
- Python 3.13
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- Pydantic
- Jinja2
- Starlette
- Argon2
- Pytest
- HTTPX

## Installation

1. Create a virtual environment:
   `python -m venv venv`

2. Activate the environment:
   `.\venv\Scripts\Activate.ps1`

3. Install dependencies:
   `python -m pip install -r requirements.txt`

4. Configure the session secret:
   `$env:SECUREDOC_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(32))")`

5. Start the application:
   `uvicorn app.main:app --reload`

Open `http://127.0.0.1:8000`.

## Environment Variables
- `SECUREDOC_SECRET_KEY`: Required session secret.
- `SECUREDOC_HTTPS_ONLY`: Set to `true` when deployed using HTTPS.

## Database
SQLite database (`securedoc.db`). Tables are initialized automatically at startup.

## Tests
Run `python -m pytest -q`.

## Project Status
Core implementation and automated tests completed. Deployment and final verification pending.
