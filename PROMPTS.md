# SecureDoc - AI Prompt Log

## Purpose
This file records AI-assisted development for the Snovasys Fresher Hiring Challenge 2026. It documents prompts, expected outputs, review criteria, corrections, and implementation status. Features are marked complete only after code review and verification.

## Project Planning and Architecture

### Entry 1 - Requirements and Implementation Planning

**Prompt used:**
Help me break down the SecureDoc challenge requirements into an implementation plan. Include authentication, authorization, secure document storage, audit logging, testing, security, documentation, and submission deliverables. Do not mark features complete before implementation and verification.

**Expected output:**
A structured implementation roadmap and project documentation outline.

**Review and correction:**
Requirements were documented and checked against the challenge scope. Implementation status is tracked separately from proposed work.

## Security Threat Modelling

### Entry 2 - Threat Model

**Prompt used:**
Identify realistic security threats for a secure document-sharing application. Consider IDOR, unauthorized downloads, permission revocation, file upload validation, audit log tampering, search information leakage, excessive privileges, session abuse, SQL injection, XSS, brute-force attacks, and AI permission suggestions. For each threat, describe mitigations and verification tests. Do not claim a mitigation is implemented unless code and tests prove it.

**Expected output:**
A threat model containing threats, mitigations, and verification criteria.

**Review and correction:**
Threats and mitigations are documented in THREATS.md. Implementation status is distinguished from planned security controls.

## Authentication and Session Management

### Entry 3 - User Authentication

**Prompt used:**
Implement secure user registration and login for SecureDoc. Validate usernames and email addresses, prevent duplicates, hash passwords using Argon2, enforce password length requirements, block common passwords, handle invalid credentials, manage authenticated sessions, protect dashboard routes, and implement logout. Include tests and do not expose passwords or secrets.

**Expected output:**
Registration, login, password hashing, session handling, logout, and protected routes.

**Review and correction:**
Registration, validation, duplicate prevention, Argon2 hashing, password checks, login, session handling, logout, and dashboard protection were implemented and tested.

## Document Authorization

### Entry 4 - Document-Level Access Control

**Prompt used:**
Implement centralized server-side authorization for SecureDoc documents. Verify ownership and document permissions on every protected operation. Support Viewer and Editor access levels, prevent viewers from editing, allow owners to grant and revoke permissions, and ensure revoked or unshared users immediately lose access. Add automated authorization tests.

**Expected output:**
Centralized authorization and document-level permission management.

**Review and correction:**
Ownership verification, Viewer and Editor permissions, permission granting and revocation, and access denial after revocation were implemented and covered by authorization tests.

## Secure Document Management

### Entry 5 - Upload and Download Security

**Prompt used:**
Implement secure document upload and download APIs. Sanitize filenames, enforce a maximum upload size of 200 MB, validate supported file types and file signatures, store uploaded files privately, authorize downloads on the server, and provide owned and shared document listings. Add API integration tests.

**Expected output:**
Secure upload, download, validation, and document listing functionality.

**Review and correction:**
Upload validation, filename sanitization, private storage, authorized downloads, document listings, and unauthorized request handling were implemented and tested.

## Audit Logging

### Entry 6 - Audit Logging Implementation

**Prompt used:**
Create an AuditLog database model and audit_logs table. Implement a centralized audit logging service that records successful document uploads, download requests, permission grants, permission updates, and permission revocations. Store actor, document, action, outcome, details, IP address, and timestamp. Add isolated unit tests.

**Expected output:**
A reusable audit logging service, database model, and tests.

**Review and correction:**
The audit model, database table, centralized service, successful upload and download-request events, permission grant/update/revoke events, and audit unit tests were implemented. Denied access logging and append-only audit protection remain pending.

## Testing and Verification

### Entry 7 - Automated Test Verification

**Prompt used:**
Review and test SecureDoc authentication, document authorization, document APIs, and audit logging. Verify permission revocation, upload and download behavior, permission grant and revoke, and rejection of unauthenticated access. Report actual test results without inventing successful outcomes.

**Expected output:**
Automated tests covering implemented security and document-management functionality.

**Review and correction:**
The complete automated test suite passed: 13 tests. Two FastAPI startup-event deprecation warnings were reported; they were warnings, not test failures.

## Commit Reference

**Commit:** 8259e6b
**Message:** Implement secure authentication, document authorization and audit logging

## Pending Work

- Log denied document access and denied permission attempts.
- Add audit events for document edits and deletions when those operations are implemented.
- Enforce append-only audit protection.
- Implement an admin activity API and dashboard.
- Implement AI permission suggestions with explicit document-owner approval.
- Perform final security testing and deployment verification.

## Reusable AI Instructions

- Do not invent completed work, test results, or deployment status.
- Prioritize server-side authorization and data confidentiality.
- Explain security-sensitive code before proposing changes.
- Identify assumptions, limitations, and potential failure cases.
- Preserve existing source code and database contents.
- Require human review and explicit owner approval for AI-generated permission suggestions.
