# SecureDoc API Documentation

## Overview

SecureDoc is a secure document management application built with FastAPI.
Routes are registered without an `/api` prefix.

All protected operations require server-side authentication and authorization.
Mutating requests are subject to CSRF protection.

## Authentication

### POST /auth/register
Register a new account.

- Request: username, email, password, role.
- Allowed registration roles: `owner`, `viewer`.
- Default role: `owner`.
- Success: `201 Created`.
- Duplicate username or email: `409 Conflict`.

### POST /auth/login
Authenticate using email and password.

- Success: establishes a session.
- Invalid credentials: `401 Unauthorized`.
- Inactive account: `403 Forbidden`.
- Rate limit exceeded: `429 Too Many Requests`.

### GET /auth/me
Return the authenticated user's account information.

### POST /auth/logout
Clear the current session.

## Documents

### POST /documents/upload
Upload a document.

- Access: Owner or Admin.
- Request: multipart/form-data.
- Required field: `file`.
- Optional field: `category` (default: `General`).
- Maximum file size: 200 MB.
- Supported formats: PDF, TXT, PNG, JPG, JPEG, DOCX, PPT, PPTX.
- Success: `201 Created`.

### GET /documents/
List documents accessible to the authenticated user.

Supported query parameters:

- `q`: search by filename, content type, category, or owner details.
- `content_type`: filter by content type.
- `category`: filter by category.
- `ownership`: `all`, `owned`, or `shared`.
- `date_from`, `date_to`: date filters in YYYY-MM-DD format.
- `sort_by`: `filename`, `created_at`, or `file_size`.
- `sort_order`: `asc` or `desc`.
- `limit`: 1–100 (default 100).
- `offset`: zero or greater (default 0).

Results are filtered according to the user's access rights.

### GET /documents/{document_id}/edit
Retrieve editable TXT document content.

- Access: Owner/Admin or authorized editor.
- TXT files only.
- Maximum editable size: 5 MB.

### PUT /documents/{document_id}/edit
Update TXT document content.

- Access: Owner/Admin or authorized editor.
- Request JSON: `{"content": "updated text"}`.
- TXT files only.
- Maximum content size: 5 MB.

### PUT /documents/{document_id}/replace
Replace an existing document file.

- Access: Owner/Admin or authorized editor.
- Request: multipart/form-data with `file`.
- Replacement must use the same supported file extension.
- Maximum file size: 200 MB.

### GET /documents/{document_id}/preview
Preview a supported document.

- Access: authenticated users with document viewing permission.
- Supported formats: PDF, PNG, JPG, JPEG, TXT, PPT, PPTX.
- PPT/PPTX preview requires LibreOffice conversion.

### GET /documents/{document_id}/download
Download the original document.

- Access: authenticated users with document viewing permission.

### GET /documents/{document_id}/users/search
Search active users for document sharing.

- Access: Document Owner or Admin.
- Query parameter: `q` (minimum 2 characters).
- Excludes the current user.

### GET /documents/{document_id}/permissions
List users who have access to a document.

- Access: Document Owner or Admin.

### POST /documents/{document_id}/permissions
Grant or update document access.

- Access: Document Owner or Admin.
- Request JSON: `{"user_id": 2, "access_level": "viewer"}`.
- Access levels: `viewer`, `editor`.
- Target user must be active and cannot be the current user.

### DELETE /documents/{document_id}/permissions/{target_user_id}
Revoke a user's document access.

- Access: Document Owner or Admin.

### DELETE /documents/{document_id}
Delete a document.

- Access: Document Owner or Admin.

## Roles and Permissions

### Account roles

- `admin`: administrative operations.
- `owner`: upload and manage owned documents.
- `viewer`: view documents explicitly shared with the account.

Registration does not allow users to create Admin accounts.

### Document access levels

- `viewer`: view, preview, and download.
- `editor`: edit TXT content and replace files, subject to account-role restrictions.

A Viewer account remains read-only even if a document permission record specifies `editor`.

## Administration

### GET /admin/activity
Retrieve audit activity.

- Access: Admin only.
- Query parameters:
  - `outcome`: `success` or `denied`.
  - `action`: filter by action (maximum 50 characters).
  - `actor_user_id`: filter by actor.
  - `limit`: 1–100 (default 50).
  - `offset`: zero or greater (default 0).
- Returns total count, pagination details, and activity items.

### GET /admin/overview
Retrieve administrative summary counts.

- Access: Admin only.
- Returns total users, total documents, total events, successful events, and denied events.

## Security Notes

- Document access is enforced on the server.
- Document IDs are not authorization credentials.
- Uploaded files are stored using generated filenames in private storage.
- File type, MIME type, signature, and size are validated.
- Download and preview responses use protective cache and content headers.
- Audit events record relevant successful and denied operations.
- Revoked permissions must no longer grant access.
- Frontend visibility controls are not security boundaries.

## Common HTTP Status Codes

- `200 OK`: Request succeeded.
- `201 Created`: Resource created.
- `400 Bad Request`: Invalid request.
- `401 Unauthorized`: Authentication required or invalid credentials.
- `403 Forbidden`: Access denied or account inactive.
- `404 Not Found`: Resource not found.
- `409 Conflict`: Duplicate account details.
- `415 Unsupported Media Type`: Unsupported file type.
- `422 Unprocessable Entity`: Validation or processing failure.
- `429 Too Many Requests`: Rate limit exceeded.
- `500 Internal Server Error`: Unexpected server error.
- `503 Service Unavailable`: Preview service unavailable.
- `504 Gateway Timeout`: Preview conversion timed out.

## Documentation Status

This document describes the implemented application routes and their verified behavior.
