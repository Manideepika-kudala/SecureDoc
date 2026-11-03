# SecureDoc API Documentation

## Overview
SecureDoc provides secure document management and sharing through authenticated API endpoints.

All document operations must enforce server-side authorization.

## Authentication

### POST /api/auth/register
Register a user account.

### POST /api/auth/login
Authenticate a user and establish a session.

### POST /api/auth/logout
End the current session.

## Documents

### POST /api/documents
Upload a document.

Allowed roles: Owner

### GET /api/documents
List documents accessible to the authenticated user.

Allowed roles: Admin, Owner, Viewer

### GET /api/documents/{documentId}
View document metadata.

Allowed roles: Admin, Owner, explicitly authorized users

### GET /api/documents/{documentId}/download
Download a document.

Allowed roles: Owner, users with READ or EDIT permission

### PUT /api/documents/{documentId}
Update document metadata or content.

Allowed roles: Owner, users with EDIT permission

### DELETE /api/documents/{documentId}
Delete a document.

Allowed roles: Owner

## Permissions

### POST /api/documents/{documentId}/permissions
Grant document access to a named user.

Allowed roles: Owner

### DELETE /api/documents/{documentId}/permissions/{userId}
Revoke document access.

Allowed roles: Owner

## Search

### GET /api/documents/search
Search by document name, owner, category, and date.

Allowed roles: Authenticated users

Search results must be filtered by authorization.

## Audit

### GET /api/admin/audit
View audit records.

Allowed roles: Admin

### GET /api/admin/activity
View document activity.

Allowed roles: Admin

## Authorization Requirements

- Every document endpoint must validate access on the server.
- Document IDs must not be treated as authorization credentials.
- Unauthorized requests must not reveal document contents.
- Denied access attempts must be recorded in the audit trail.
- Revoked permissions must stop granting access immediately.
- Frontend visibility checks are not security controls.

## Status Codes

- 200 OK: Request succeeded.
- 201 Created: Resource created.
- 400 Bad Request: Invalid input.
- 401 Unauthorized: Authentication required.
- 403 Forbidden: Access denied.
- 404 Not Found: Resource does not exist.
- 500 Internal Server Error: Unexpected server failure.

## Implementation Status

This document describes the planned API contract. Endpoint availability and behavior must be verified against the implemented application.
