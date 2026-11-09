# SecureDoc - Security Threat Model

**Project:** SecureDoc
**Application:** Secure Document Management and Sharing System

---

## 1. Purpose

This document identifies security threats affecting SecureDoc, evaluates their potential impact, records existing security controls and identifies improvements required.

The assessment focuses on authentication, authorization, document storage, file handling, sharing permissions, administrative access and audit logging.

**Status Definitions:**
- Implemented: A corresponding security control exists.
- Partially Implemented: Some controls exist, but additional work is required.
- Pending: Implementation or verification is not confirmed.
- Requires Review: Additional security testing is necessary.

---

## 2. Threat Assessment

### T01 - Broken Access Control / IDOR

**Category:** Authorization

**Threat Description:**
An authenticated user may attempt to access another user's document by manipulating document identifiers or request parameters.

**Attack Scenario:**
An attacker changes a document ID in a URL or API request to access a document they do not own or have permission to view.

**Potential Impact:**
- Unauthorized document disclosure.
- Exposure of confidential information.
- Violation of document ownership boundaries.

**Existing Mitigation:**
- Centralized server-side authorization.
- Document ownership verification.
- Permission checks for protected document operations.

**Current Status:** Implemented; continued security testing recommended.

**Recommended Improvement:**
Add additional IDOR tests covering every document-related endpoint and identifier manipulation scenario.

---

### T02 - Unauthorized Document Download

**Category:** File Access Security

**Threat Description:**
An unauthorized user may attempt to download documents without valid ownership or sharing permissions.

**Attack Scenario:**
An attacker sends a direct download request for a document belonging to another user.

**Potential Impact:**
Disclosure of confidential documents.

**Existing Mitigation:**
- Private document storage.
- Server-side authorization.
- Ownership and sharing-permission verification.

**Current Status:** Implemented for protected download operations.

**Recommended Improvement:**
Test direct URL access, manipulated identifiers and unauthorized download requests.

---

### T03 - Access After Permission Revocation

**Category:** Permission Management

**Threat Description:**
A user whose document-sharing permission has been revoked may attempt to retain access.

**Attack Scenario:**
A previously authorized user attempts another download or document operation after the owner revokes access.

**Potential Impact:**
Continued unauthorized access to private documents.

**Existing Mitigation:**
- Permission revocation functionality.
- Server-side authorization checks.
- Access denial after revocation tested.

**Current Status:** Implemented and tested.

**Recommended Improvement:**
Verify that every protected operation checks current permissions rather than relying on stale authorization information.

---

### T04 - Excessive Document Privileges

**Category:** Privilege Management

**Threat Description:**
A shared user may receive more permissions than required.

**Attack Scenario:**
A Viewer attempts an operation intended for an Editor or document owner.

**Potential Impact:**
Unauthorized document modification or management.

**Existing Mitigation:**
- Viewer and Editor permission levels.
- Document ownership verification.
- Server-side permission checks.

**Current Status:** Permission levels implemented.

**Limitation:**
Complete document-editing functionality is not confirmed.

**Recommended Improvement:**
Test permission boundaries for every document operation and implement editing controls only with explicit authorization.

---

### T05 - Session Hijacking and Session Abuse

**Category:** Authentication

**Threat Description:**
An attacker may attempt to misuse an authenticated session.

**Attack Scenario:**
An attacker obtains or reuses a session identifier to impersonate an authenticated user.

**Potential Impact:**
Unauthorized account and document access.

**Existing Mitigation:**
- Session management.
- Protected authenticated routes.
- Logout functionality.

**Current Status:** Partially Implemented.

**Recommended Improvement:**
Review:
- Secure cookie configuration.
- HttpOnly and SameSite attributes.
- Session expiration.
- Session identifier regeneration.
- Session invalidation after logout.
- HTTPS deployment requirements.

---

### T06 - Malicious File Upload

**Category:** File Security

**Threat Description:**
An attacker may upload a malicious or disguised file.

**Attack Scenario:**
An attacker uploads a file with a misleading extension, invalid content or potentially dangerous payload.

**Potential Impact:**
- Application compromise.
- Storage of malicious content.
- Security vulnerabilities affecting users.

**Existing Mitigation:**
- Filename sanitization.
- File validation.
- File-size and file-type checks.

**Current Status:** Partially Implemented.

**Limitation:**
Malware scanning is not confirmed.

**Recommended Improvement:**
Introduce malware scanning, strict file validation, storage isolation and upload security testing.

---

### T07 - Public Exposure of Stored Documents

**Category:** Data Confidentiality

**Threat Description:**
Private documents may become publicly accessible because of incorrect storage configuration.

**Attack Scenario:**
An attacker attempts to access stored files through a publicly exposed directory or predictable file path.

**Potential Impact:**
Unauthorized disclosure of sensitive documents.

**Existing Mitigation:**
Documents are stored in private storage rather than intentionally exposed through public static directories.

**Current Status:** Application-level private storage implemented.

**Recommended Improvement:**
Verify filesystem permissions, deployment configuration, backup protection and production storage isolation.

---

### T08 - Audit Log Tampering

**Category:** Audit Integrity

**Threat Description:**
An attacker or privileged user may attempt to modify or delete audit records.

**Attack Scenario:**
An attacker changes historical activity records to hide unauthorized operations.

**Potential Impact:**
- Loss of accountability.
- Investigation difficulties.
- Reduced trust in audit records.

**Existing Mitigation:**
- AuditLog database model.
- Centralized audit logging service.

**Current Status:** Partially Implemented.

**Limitation:**
Append-only and tamper-evident protection are not confirmed.

**Recommended Improvement:**
Implement restricted audit modification, append-only storage and tamper-evident verification.

---

### T09 - User and Document Search Information Leakage

**Category:** Information Disclosure

**Threat Description:**
Search functionality may expose information about users or documents beyond the intended scope.

**Attack Scenario:**
An attacker manipulates search queries to discover unauthorized user or document information.

**Potential Impact:**
- User information disclosure.
- Document metadata exposure.
- Privacy violations.

**Existing Mitigation:**
User search and document-sharing functionality are implemented.

**Current Status:** Requires Security Review.

**Recommended Improvement:**
Verify search authorization, result filtering, input validation and minimum necessary response fields.

---

### T10 - SQL Injection

**Category:** Input and Database Security

**Threat Description:**
An attacker may attempt to inject malicious SQL through user-controlled input.

**Attack Scenario:**
An attacker submits specially crafted input through authentication, search or document-related endpoints.

**Potential Impact:**
- Unauthorized database access.
- Data modification.
- Data disclosure.

**Existing Mitigation:**
The application uses a database-backed data-access layer.

**Current Status:** Dedicated SQL injection security testing is pending.

**Recommended Improvement:**
Review ORM usage, avoid unsafe query construction and perform dedicated injection testing.

---

### T11 - Cross-Site Scripting (XSS)

**Category:** Web Application Security

**Threat Description:**
An attacker may attempt to inject malicious scripts into application pages.

**Attack Scenario:**
An attacker submits malicious content through username, filename or other user-controlled fields.

**Potential Impact:**
- Script execution in another user's browser.
- Session-related attacks.
- Unauthorized actions through the victim's browser.

**Existing Mitigation:**
Frontend templates and user-facing document information are implemented.

**Current Status:** Dedicated XSS verification is pending.

**Recommended Improvement:**
Review template escaping, output encoding, input handling and Content Security Policy.

---

### T12 - Unauthorized Permission Modification

**Category:** Authorization

**Threat Description:**
A user may attempt to grant, update or revoke document permissions without being the owner.

**Attack Scenario:**
An attacker sends a manipulated permission-management request for another user's document.

**Potential Impact:**
- Unauthorized access grants.
- Loss of document confidentiality.
- Disruption of legitimate sharing.

**Existing Mitigation:**
- Server-side ownership verification.
- Permission grant, update and revoke operations.

**Current Status:** Implemented; additional negative testing recommended.

**Recommended Improvement:**
Test unauthorized permission changes and record denied attempts in the audit log.

---

### T13 - Incomplete Audit Trail

**Category:** Security Monitoring

**Threat Description:**
Important security events may not be recorded.

**Attack Scenario:**
An attacker performs denied access attempts or unauthorized permission changes that are not recorded.

**Potential Impact:**
Incomplete security investigations and reduced accountability.

**Existing Mitigation:**
Audit logging records document uploads, download requests and permission activities.

**Current Status:** Partially Implemented.

**Recommended Improvement:**
Add logging for denied access, authentication failures and rejected permission changes. Avoid recording passwords or sensitive secrets.

---

### T14 - Brute-Force Login Attacks

**Category:** Authentication Security

**Threat Description:**
An attacker may repeatedly attempt login using different password combinations.

**Attack Scenario:**
Automated requests repeatedly target the login endpoint.

**Potential Impact:**
- Account compromise.
- Authentication service abuse.
- Increased server resource consumption.

**Existing Mitigation:**
- Argon2 password hashing.
- User authentication and validation.

**Current Status:** Rate limiting is pending.

**Recommended Improvement:**
Introduce rate limiting, appropriate monitoring and carefully designed authentication failure handling.

---

### T15 - Unsafe AI Permission Suggestions

**Category:** AI and Access Control

**Threat Description:**
An AI-based recommendation system may suggest inappropriate document permissions.

**Attack Scenario:**
An AI system recommends granting access to an unintended user or assigning an excessive permission level.

**Potential Impact:**
Unauthorized document disclosure or excessive privileges.

**Existing Mitigation:**
No completed AI permission recommendation workflow is confirmed.

**Current Status:** Pending.

**Recommended Improvement:**
Require explicit document-owner approval before applying any AI-generated permission suggestion.

---

### T16 - Administrative Privilege Escalation

**Category:** Administrative Security

**Threat Description:**
A normal user may attempt to access administrative functionality.

**Attack Scenario:**
An attacker directly accesses admin routes or manipulates administrative API requests.

**Potential Impact:**
- Unauthorized administrative operations.
- Access to privileged information.
- Application-level compromise.

**Existing Mitigation:**
- Admin dashboard.
- Admin API.
- Admin-related automated tests.

**Current Status:** Implemented; additional authorization review required.

**Recommended Improvement:**
Verify server-side administrator checks, non-admin rejection and privilege boundaries for every admin endpoint.

---

### T17 - Sensitive Metadata Exposure

**Category:** Privacy and Information Disclosure

**Threat Description:**
Document-sharing metadata may expose more user information than necessary.

**Attack Scenario:**
An attacker accesses sharing details or API responses containing unnecessary user information.

**Potential Impact:**
- User privacy violations.
- Exposure of sharing relationships.
- Unnecessary disclosure of account information.

**Existing Mitigation:**
The dashboard displays sharing details such as shared-by username, email, date/time and access level.

**Current Status:** Requires Security Review.

**Recommended Improvement:**
Review API response fields and ensure users receive only metadata necessary for their authorized operations.

---

## 3. Security Control Summary

| Security Area | Existing Control | Remaining Work |
|---|---|---|
| Authentication | Registration, login, Argon2 | Rate limiting and session review |
| Authorization | Ownership and permission checks | Expanded negative testing |
| Document Upload | Validation and sanitization | Malware scanning |
| Document Storage | Private application storage | Production configuration review |
| Document Download | Protected download operations | Expanded access testing |
| Sharing | Viewer and Editor permissions | Complete editing verification |
| Permission Revocation | Revocation and access denial | Broader operation testing |
| Admin | Admin dashboard and API | Privilege-boundary review |
| Audit Logging | Centralized audit service | Denied events and tamper protection |
| AI Permissions | No completed workflow confirmed | Owner-approved recommendations |

---

## 4. Testing and Verification Record

**Recorded Test Command:**

    python -m pytest -q

**Recorded Result:**

    22 passed, 2 warnings in 6.54s

**Warnings:**
Two FastAPI startup-event deprecation warnings associated with `@app.on_event("startup")`.

**Interpretation:**
All 22 tests passed in the recorded run. This result does not establish that every threat listed in this document has been fully tested or eliminated.

---

## 5. Known Security Limitations

1. Complete document-editing functionality is not confirmed.
2. Malware scanning is not confirmed.
3. Append-only or tamper-evident audit protection is pending.
4. Denied-access audit logging requires improvement.
5. Login rate limiting is pending.
6. Dedicated XSS and SQL injection testing is pending.
7. Production security hardening requires verification.
8. Administrative authorization requires additional review.
9. Search and metadata exposure require security review.
10. Automated test coverage does not guarantee the absence of vulnerabilities.

---

## 6. Recommended Security Priorities

### High Priority
- Verify authorization on every protected document operation.
- Test IDOR and unauthorized download scenarios.
- Implement login rate limiting.
- Review session and cookie security.
- Review admin privilege boundaries.

### Medium Priority
- Introduce malware scanning.
- Implement denied-access audit logging.
- Add tamper-evident audit protection.
- Perform dedicated XSS and SQL injection tests.
- Review search and metadata exposure.

### Future Enhancements
- AI-assisted permission suggestions with explicit owner approval.
- Expanded security monitoring.
- Production deployment security verification.
- FastAPI lifespan migration.

---

## 7. Git and Project Verification Record

**Branch:** main

**Latest Recorded Commit:** e87a7ce

**Commit Message:**
feat: improve SecureDoc UI and document sharing management

**Recorded Commit Statistics:**
- 14 files changed.
- 2428 insertions.
- 68 deletions.

---

## 8. Threat Model Maintenance

This document should be updated whenever:
- A new feature changes the application's attack surface.
- A security vulnerability is discovered.
- A security control is implemented or modified.
- A threat is tested and its status changes.
- Production deployment configuration changes.

Threats must not be marked resolved solely because a feature exists. Resolution requires appropriate implementation review and verification.

**End of Security Threat Model**

---

## 9. Current Implementation Status and Updated Mitigations

This section supersedes older threat statuses where newer implementation work has changed the security controls.

| Threat | Current Control | Current Status |
|---|---|---|
| T01 Broken Access Control / IDOR | Centralized server-side ownership and permission checks | Implemented; broader endpoint testing remains |
| T02 Unauthorized Document Download | Private storage and authorized download route | Implemented; expanded negative testing remains |
| T03 Access After Permission Revocation | Current permission checks and revocation behavior | Implemented; additional operation coverage remains |
| T04 Excessive Document Privileges | Viewer and Editor permission checks | Partially implemented; complete editing capability is not confirmed |
| T05 Session Hijacking and Session Abuse | Session management, logout and session-version invalidation | Partially implemented; cookie and lifecycle review remains |
| T06 Malicious File Upload | Extension, MIME, signature, size and Office archive validation | Partially implemented; malware scanning is not confirmed |
| T07 Public Exposure of Stored Documents | Private application storage and protected download routes | Implemented at application level; filesystem and production configuration require review |
| T08 Audit Log Tampering | SQLite triggers prevent ordinary audit UPDATE and DELETE operations | Partially implemented; direct database-file access is not protected |
| T09 Search Information Leakage | User-search input validation and SQL injection test | Requires broader authorization and metadata review |
| T10 SQL Injection | Parameterized ORM-based access and a passing user-search injection test | Partially tested; other query paths require review |
| T11 Cross-Site Scripting | Template escaping checks and preliminary unsafe-rendering review | Partially reviewed; comprehensive XSS testing remains |
| T12 Unauthorized Permission Modification | Owner checks and denied audit events for non-owner permission actions | Implemented for tested operations; broader tests remain |
| T13 Incomplete Audit Trail | Authentication and document activity audit events, including tested denials | Partially implemented; complete route coverage remains |
| T14 Brute-Force Login Attacks | Login rate limiting and targeted test | Implemented; broader abuse testing remains |
| T15 Unsafe AI Permission Suggestions | No completed AI permission recommendation workflow confirmed | Pending |
| T16 Administrative Privilege Escalation | Protected admin functionality and admin API tests | Implemented; additional privilege-boundary review remains |
| T17 Sensitive Metadata Exposure | Sharing metadata and administrative response controls | Requires security review |

## 10. Additional Verified Security Controls

### Authentication Audit Events
Registration, login and logout success/denial events are recorded through the centralized audit service. Passwords and password hashes are not included in audit records.

### Denied Permission Operations
Non-owner attempts to view, grant and revoke document permissions have denied audit logging.

### File Upload Validation
Targeted tests cover:
- MIME-type mismatch.
- Empty files.
- Invalid DOCX archives.
- Invalid PPTX structures.
- Files exceeding the configured size limit.

### Download Response Protection
Download responses are checked for:
- Attachment content disposition.
- X-Content-Type-Options: nosniff.
- Cache-Control: private, no-store, max-age=0.
- Pragma: no-cache.

### Rate Limiting
The custom HTTP exception handler preserves response headers supplied by the exception, including Retry-After.

### Error Handling
Validation errors use structured responses. Unexpected server errors are logged internally and return generic client-facing messages.

### Audit Database Protection
SQLite triggers prevent ordinary UPDATE and DELETE operations on audit records. This is not equivalent to cryptographically tamper-proof or externally immutable audit storage.

## 11. Remaining Security Work

1. Expand IDOR and authorization tests across all protected endpoints.
2. Verify permission boundaries for all Viewer and Editor operations.
3. Review session-cookie security, expiration and invalidation.
4. Evaluate malware scanning.
5. Review filesystem permissions and storage isolation.
6. Evaluate stronger audit integrity for direct database-file access.
7. Expand SQL injection tests beyond user search.
8. Complete XSS testing for dynamic and stored user-controlled content.
9. Review CSRF coverage across state-changing endpoints.
10. Expand denied-access audit coverage.
11. Review administrative privilege boundaries.
12. Review search responses and metadata exposure.
13. Run a fresh complete test suite after recent changes.

## 12. Assessment Limitations

- A passing targeted test establishes only the behavior covered by that test.
- Existing security controls do not prove the absence of all vulnerabilities.
- Private application storage does not by itself establish secure production filesystem configuration.
- SQLite triggers do not prevent a person with direct database-file access from replacing or modifying the database.
- Malware scanning is not confirmed.
- AI permission suggestions are not confirmed as implemented.
- Complete document editing functionality is not confirmed.

**End of Updated Security Assessment**
