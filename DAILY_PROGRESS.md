# SecureDoc - Project Progress

## Completed Work

### Authentication
- User registration and login.
- Username and email validation.
- Argon2 password hashing.
- Session management and logout.
- Protected dashboard routes.

### Document Authorization
- Centralized server-side authorization.
- Document ownership verification.
- Viewer and Editor permission levels.
- Permission grant, update and revoke.
- Access denial after permission revocation.

### Document Management
- Secure document upload and download.
- Filename sanitization and file validation.
- Private document storage.
- My Documents and Shared With Me sections.
- Shared-by username, email and date/time display.

### Document Sharing
- Dedicated sharing page.
- User search by username/email.
- Viewer and Editor permission selection.
- Permission update and revoke.

### Dashboard and Admin
- Updated dashboard UI and CSS.
- Dynamic document rendering.
- Loading, empty and error states.
- Admin dashboard and API.
- Admin API tests.

### Audit Logging
- AuditLog model and database table.
- Centralized audit logging.
- Upload, download-request and permission activity logging.

## Testing
- Full test suite: 22 passed.
- 2 FastAPI deprecation warnings.
- Command: python -m pytest -q

## Latest Git Commit
- Branch: main
- Commit: e87a7ce
- Message: feat: improve SecureDoc UI and document sharing management
- Files committed: 14

## Pending Work
- Denied access audit logging.
- Append-only audit protection.
- Admin authorization review.
- AI permission suggestions with owner approval.
- Login rate limiting.
- XSS and SQL injection security testing.
- Production security verification.
- FastAPI lifespan migration.
- Review unstaged deletion of app/_init_.py.

## Limitations
- Complete document editing is not confirmed.
- Malware scanning is not confirmed.
- Production security hardening remains pending.
