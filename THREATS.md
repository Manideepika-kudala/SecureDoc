# SecureDoc - Threat Model

## Project
SecureDoc - Snovasys Fresher Hiring Challenge 2026

## Security Objective
Ensure that only authenticated and explicitly authorized users can access documents, protect uploaded files, enforce document-level permissions, and maintain a reliable record of security-relevant activity.

## Implementation Status
- Implemented: Controls supported by current application code and automated tests.
- Pending: Controls that still require implementation or verification.
- Proposed: Additional controls that require design and implementation.

## Threats, Mitigations and Status

### T01 - Insecure Direct Object Reference (IDOR)
**Threat:** An attacker changes a document ID in a URL or API request to access another user's document.

**Mitigation:** Perform centralized server-side ownership and permission checks on protected document operations.

**Status:** Implemented. Authorization service tests and document API integration tests cover access control.

### T02 - Unauthorized Download
**Threat:** An unauthenticated or unauthorized user accesses a document.

**Mitigation:** Keep uploaded files in private storage and require server-side authorization before returning a file.

**Status:** Implemented. Download authorization and unauthorized request handling are covered by tests.

### T03 - Permission Revocation Failure
**Threat:** A user retains access after their document permission has been revoked.

**Mitigation:** Re-check current document permissions on every protected operation instead of relying on stale authorization data.

**Status:** Implemented. Permission revocation behavior is covered by automated tests.

### T04 - Excessive Privileges
**Threat:** A Viewer performs operations that require Editor or owner privileges.

**Mitigation:** Enforce Viewer and Editor permissions on the server. Restrict permission management to document owners.

**Status:** Implemented for the current document authorization operations.

### T05 - Session Abuse
**Threat:** A stolen or improperly managed session is used to access a user's account.

**Mitigation:** Use authenticated sessions, secure session configuration, protected routes, and logout functionality. Production cookie settings and session lifetime must be reviewed before deployment.

**Status:** Basic session handling, logout, and protected routes are implemented. Production hardening requires further verification.

### T06 - File Upload Validation Bypass
**Threat:** An attacker uploads an unsupported, oversized, or disguised file.

**Mitigation:** Sanitize filenames, enforce the 200 MB upload limit, validate supported file types and file signatures, and store files privately.

**Status:** Implemented and covered by document API tests. Malware scanning is not currently confirmed.

### T07 - Public Storage Exposure
**Threat:** A document is accessed directly through a public storage path.

**Mitigation:** Store documents outside public web directories and serve them through authorized application endpoints.

**Status:** Private application storage and authorized download handling are implemented. Production storage permissions require deployment verification.

### T08 - Audit Trail Tampering
**Threat:** An attacker or privileged user modifies or deletes audit records to hide activity.

**Mitigation:** Apply append-only controls, restrict database access, and consider integrity verification or external audit storage.

**Status:** Pending. The audit model and logging service exist, but append-only protection and tamper-evidence controls are not yet implemented.

### T09 - Search Information Leakage
**Threat:** Search results expose document names or metadata to unauthorized users.

**Mitigation:** Apply ownership and permission filters before returning document search results.

**Status:** Requires verification when document search functionality is implemented.

### T10 - SQL Injection
**Threat:** Malicious input changes database queries.

**Mitigation:** Use SQLAlchemy ORM operations and parameterized database queries. Avoid constructing SQL statements through unsafe string concatenation.

**Status:** ORM-based database access is used. Dedicated SQL injection security testing remains pending.

### T11 - Cross-Site Scripting (XSS)
**Threat:** Malicious document metadata or user input executes in another user's browser.

**Mitigation:** Escape rendered output, validate input, and avoid unsafe HTML rendering.

**Status:** Requires dedicated security review and XSS testing.

### T12 - Unauthorized Permission Changes
**Threat:** A user grants, updates, or revokes permissions without ownership or authorization.

**Mitigation:** Verify document ownership and target-user validity on the server before changing permissions.

**Status:** Implemented for current permission grant, update, and revoke operations.

### T13 - Audit Log Gaps
**Threat:** Denied access attempts and other security-relevant failures are not recorded.

**Mitigation:** Record both successful and denied security events, including actor, document, action, outcome, details, IP address, and timestamp where available.

**Status:** Successful upload, download-request, permission grant, update, and revoke events are implemented. Denied access and denied permission attempt logging remain pending.

### T14 - Brute Force Login
**Threat:** Repeated login attempts are used to guess account passwords.

**Mitigation:** Use Argon2 password hashing, reject common passwords, and introduce login rate limiting and monitoring.

**Status:** Argon2 hashing and common-password checks are implemented. Login rate limiting requires implementation and verification.

### T15 - AI Permission Suggestion Abuse
**Threat:** AI-generated suggestions automatically grant access to confidential documents or recommend inappropriate users.

**Mitigation:** Treat AI output only as a suggestion. Require explicit document-owner approval before any permission is granted.

**Status:** Pending. AI permission suggestions and owner approval workflow are not yet implemented.

## Additional Pending Security Work

- Add audit events for document edits and deletions when those operations exist.
- Implement append-only audit protection.
- Implement an admin activity API and dashboard with appropriate access controls.
- Perform dedicated security tests for session configuration, SQL injection, XSS, and brute-force protection.
- Verify file storage permissions and security configuration in the deployment environment.

## Known Trade-offs and Limitations

- Download requests are logged when an authorized download is initiated; this does not prove that the complete file transfer succeeded.
- Application-level audit logging alone does not guarantee tamper-proof records.
- Without malware scanning, the application cannot guarantee detection of every malicious upload.
- Production security depends on correct deployment configuration, secret management, HTTPS, database permissions, and storage permissions.
- Search-related protections must be verified against the actual search implementation.

## Verification

The current automated test suite passed 13 tests covering authorization, document API behavior, and audit logging.

Passing automated tests do not establish that every threat listed above is fully mitigated. Pending controls and deployment-specific protections require separate implementation and verification.
