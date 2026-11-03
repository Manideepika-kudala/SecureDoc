# SecureDoc - Threat Model

## Project
SecureDoc - Snovasys Fresher Hiring Challenge 2026

## Security Objective
Ensure that only explicitly authorized users can access documents and maintain a trustworthy record of document activity.

## Threats and Mitigations

### T01 - Insecure Direct Object Reference (IDOR)
Threat: An attacker changes a document ID in a URL or API request to access another user's document.
Mitigation: Check document-level authorization on the server for every request.
Verification: Automated tests attempt cross-user document access.

### T02 - Unauthorized Download
Threat: A user accesses a file directly without authentication or permission.
Mitigation: Store files privately. Downloads must pass through a server-side authorization check.

### T03 - Permission Revocation Failure
Threat: A previously authorized user retains access after permission is revoked.
Mitigation: Re-check current permissions on every document operation. Avoid long-lived authorization caches.

### T04 - Excessive Privileges
Threat: A Viewer gains edit, delete, or administrative capabilities.
Mitigation: Enforce role and document permission checks server-side.

### T05 - JWT or Session Abuse
Threat: A stolen or revoked token continues to provide access.
Mitigation: Use secure token/session handling, short token lifetime, and revocation checks.

### T06 - File Upload Validation Bypass
Threat: An attacker uploads a malicious file or disguises its type.
Mitigation: Validate file extension, file signature, and size. Store uploads outside public web directories.

### T07 - Public Storage Exposure
Threat: A document is accessed using a direct storage URL.
Mitigation: Use private storage and authorize before issuing short-lived download access.

### T08 - Audit Trail Tampering
Threat: An attacker or administrator alters or deletes records to hide document access.
Mitigation: Use append-only audit storage, restricted database permissions, and integrity verification.

### T09 - Search Information Leakage
Threat: Search results reveal document names or metadata to unauthorized users.
Mitigation: Apply authorization filters in database queries before returning results.

### T10 - SQL Injection
Threat: Malicious input alters database queries.
Mitigation: Use parameterized queries and safe ORM operations.

### T11 - Cross-Site Scripting (XSS)
Threat: Malicious document metadata executes in another user's browser.
Mitigation: Escape rendered output and validate input.

### T12 - Unauthorized Permission Changes
Threat: A user grants access to documents they do not own.
Mitigation: Only document owners or explicitly authorized administrators can change permissions.

### T13 - Audit Log Gaps
Threat: Failed or denied access attempts are not recorded.
Mitigation: Log security-relevant attempts, including denied requests.

### T14 - Brute Force Login
Threat: Repeated login attempts compromise accounts.
Mitigation: Apply rate limiting and secure password hashing.

### T15 - AI Permission Suggestion Abuse
Threat: AI suggestions automatically grant access to confidential documents.
Mitigation: AI may suggest users only. The owner must explicitly approve every grant.

## Known Trade-offs
- Short-lived download links may remain valid until expiry after revocation.
- A deployment without external malware scanning cannot guarantee detection of every malicious file.
- Audit integrity depends on database and infrastructure controls.

## Verification
Threat mitigations will be verified through automated security tests and deployed-system checks. Unverified controls will not be described as complete.
