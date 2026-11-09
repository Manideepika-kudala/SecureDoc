# SecureDoc - Project Prompt Documentation

## 1. Overview

This document maintains the main development prompts and requirements associated with the SecureDoc project.

It can be used as a reference for:
- Understanding the project.
- Continuing development.
- Implementing new functionality.
- Reviewing existing functionality.
- Improving application security.
- Testing and debugging.
- Maintaining documentation.

The prompts below describe intended tasks and requirements. Their presence in this document does not mean every prompt was independently executed.

---

## 2. Master Project Prompt

**Prompt:**

Develop a secure web-based document management application named SecureDoc.

The application should provide:

1. User registration and authentication.
2. Role-based access control.
3. Owner and Viewer roles.
4. Document upload and management.
5. Document ownership enforcement.
6. Controlled document sharing.
7. Secure document access and downloads.
8. Audit logging.
9. Administrative functionality.
10. Database integration.
11. Automated testing.
12. Deployment configuration.
13. Complete project documentation.

Use a modular application architecture and apply security checks on the server side.

Do not allow users to perform operations beyond their assigned permissions.

---

## 3. Project Architecture Prompt

**Prompt:**

Review the SecureDoc application architecture and organize the project into maintainable modules.

Requirements:

- Keep authentication functionality separate from document functionality.
- Keep authorization logic reusable.
- Separate database models and application services where appropriate.
- Organize templates and static assets.
- Maintain configuration separately from application code.
- Keep tests organized by functionality.
- Avoid unnecessary duplication.
- Preserve existing functionality while implementing changes.

Before modifying an existing module, understand its dependencies and current behavior.

---

## 4. Authentication Prompt

**Prompt:**

Implement secure user registration, login, and logout functionality.

Requirements:

- Validate registration input.
- Store passwords using an appropriate secure password-hashing mechanism.
- Authenticate users before allowing protected operations.
- Handle invalid credentials safely.
- Protect authenticated sessions.
- Ensure logout invalidates the applicable session.
- Avoid exposing sensitive account information.

Add tests for successful authentication, invalid credentials, and unauthorized access.

---

## 5. Role-Based Access Control Prompt

**Prompt:**

Implement role-based authorization for SecureDoc.

The application must support two main user roles:

### Owner

The Owner role should provide permissions for document ownership and permitted document management operations.

### Viewer

The Viewer role should provide restricted access to permitted documents.

Requirements:

- Assign the user's role during account creation according to the available role-selection rules.
- Validate role values on the server.
- Enforce permissions in backend routes and services.
- Do not rely only on frontend visibility.
- Prevent Viewer users from performing Owner-only operations.
- Ensure users cannot change their own role without authorized permission.
- Validate permissions for every protected document operation.

Add authorization tests for both roles.

---

## 6. Document Management Prompt

**Prompt:**

Implement secure document management functionality.

Requirements:

- Allow permitted users to upload documents.
- Validate uploaded files.
- Store document metadata appropriately.
- Associate documents with their owners.
- Allow authorized users to list and access permitted documents.
- Restrict downloads according to permissions.
- Restrict deletion according to ownership and authorization rules.
- Handle missing documents safely.
- Prevent unauthorized access through manipulated document identifiers.

Add tests for upload, access, download, deletion, and permission enforcement.

---

## 7. Document Sharing Prompt

**Prompt:**

Implement controlled document-sharing functionality.

Requirements:

- Allow only authorized users to manage sharing.
- Associate shared access with the relevant user and document.
- Enforce Viewer restrictions.
- Validate the target user's identity and permissions.
- Support access revocation where implemented.
- Ensure revoked permissions no longer authorize document operations.
- Prevent unintended ownership transfer.
- Reject unauthorized sharing requests.

Add tests for sharing, access validation, and revocation.

---

## 8. Secure File Storage Prompt

**Prompt:**

Review the document storage implementation and improve file-handling security.

Requirements:

- Use safe file names.
- Validate uploaded file types and sizes.
- Prevent path traversal.
- Restrict access to stored files.
- Avoid exposing internal filesystem paths.
- Handle missing files safely.
- Use persistent storage in production.
- Avoid relying on temporary local storage for important documents.

Document the storage configuration and infrastructure limitations.

---

## 9. Audit Logging Prompt

**Prompt:**

Implement or improve audit logging for important application activities.

Requirements:

- Record relevant user actions.
- Associate events with the appropriate user and timestamp.
- Record relevant document-related activities.
- Restrict audit information to authorized users.
- Prevent unauthorized modification of audit records.
- Avoid storing passwords, secret keys, or unnecessary sensitive information in logs.
- Provide suitable administrative access to audit information.

Add tests for audit creation and authorization.

---

## 10. Administrative Functionality Prompt

**Prompt:**

Review and implement administrative functionality for authorized users.

Requirements:

- Restrict administrative routes.
- Validate administrative permissions on the server.
- Support permitted user-management operations.
- Provide access to relevant audit information.
- Prevent normal users from accessing administrative functionality.
- Record important administrative activities.

Add tests for authorized and unauthorized administrative requests.

---

## 11. Database Management Prompt

**Prompt:**

Review the SecureDoc database design and configuration.

Requirements:

- Maintain appropriate relationships between users and documents.
- Store role and permission information consistently.
- Maintain document ownership relationships.
- Support document-sharing relationships.
- Use safe database configuration.
- Protect database credentials.
- Support the configured development and production database environments.
- Document migration and backup considerations.

Avoid destructive database operations without explicit authorization.

---

## 12. Application Security Review Prompt

**Prompt:**

Perform a structured security review of SecureDoc.

Review the following areas:

1. Authentication.
2. Password handling.
3. Session management.
4. Role-based authorization.
5. Document ownership.
6. Document sharing.
7. File uploads.
8. File path handling.
9. Database configuration.
10. Secret management.
11. CSRF protection.
12. XSS protection.
13. Administrative access.
14. Audit logging.
15. Error handling.

For each identified issue:

- Explain the security risk.
- Identify the affected module.
- Describe the potential impact.
- Recommend an appropriate mitigation.
- Add a regression test where applicable.

Do not claim a vulnerability is fixed until the relevant implementation and test results support that conclusion.

---

## 13. Testing and Quality Assurance Prompt

**Prompt:**

Review the SecureDoc automated test suite.

Requirements:

- Test registration and login.
- Test authentication failures.
- Test Owner permissions.
- Test Viewer restrictions.
- Test document ownership.
- Test document sharing.
- Test unauthorized document access.
- Test administrative authorization.
- Test audit functionality.
- Test invalid input and error handling.
- Add regression tests for fixed defects.

Run the appropriate test commands and report actual results.

Clearly distinguish passed, failed, skipped, and unexecuted tests.

### Previously Recorded Results

- Main test suite: 81 passed.
- Audit-related test run: 17 passed.
- Python compilation check: successful.

These are historical recorded results, not a new test execution during this documentation update.

---

## 14. Debugging Prompt

**Prompt:**

Investigate the reported SecureDoc issue without unnecessarily changing unrelated functionality.

Follow this process:

1. Understand the reported error.
2. Identify the affected module.
3. Inspect relevant implementation and dependencies.
4. Reproduce the issue when possible.
5. Identify the root cause.
6. Apply the smallest appropriate fix.
7. Add or update regression tests.
8. Run the relevant tests.
9. Explain the change and actual test results.

Do not silently remove existing functionality to hide an error.

---

## 15. Deployment Prompt

**Prompt:**

Prepare SecureDoc for deployment using the configured hosting environment.

Requirements:

- Configure environment variables.
- Protect application secrets.
- Configure the production database.
- Install required dependencies.
- Configure the application startup process.
- Ensure the application uses the intended database.
- Review file-storage persistence.
- Review deployment logs.
- Check application health after deployment.
- Document hosting limitations.

Never include credentials or secret values in deployment documentation.

### Recorded Deployment Information

- Hosting provider: Render.
- Service: `securedoc-live`.
- Application URL: `https://securedoc-live.onrender.com`.
- Branch: `main`.
- Recorded deployment commit: `f13fd6c`.

These details are previously recorded project information, not a fresh deployment verification.

---

## 16. Documentation Maintenance Prompt

**Prompt:**

Maintain complete and consistent SecureDoc project documentation.

Review and update:

- `README.md`
- `IMPLEMENTATION_PLAN.md`
- `DAILY_PROGRESS.md`
- `API.md`
- `PROBLEM_STATEMENT.md`
- `THREATS.md`
- `PROMPTS.md`

Requirements:

- Describe actual application functionality accurately.
- Maintain project setup instructions.
- Document roles and permissions.
- Explain security considerations.
- Record testing results with their dates or context where available.
- Document deployment information.
- Mention known limitations.
- Avoid inventing implementation details.
- Keep documentation consistent across files.

---

## 17. Future Enhancement Prompts

The following prompts describe possible future improvements. They are not claims that these features have already been implemented.

### Multi-Factor Authentication

Explore adding an additional authentication factor to improve account security.

### Malware Scanning

Explore integrating malware scanning for uploaded documents.

### Persistent Cloud Storage

Explore an external persistent storage solution for production documents.

### Advanced Monitoring

Explore centralized application monitoring, security alerts, and operational dashboards.

### Backup and Recovery

Develop a documented backup and recovery process for application data and uploaded files.

### Security Testing

Perform periodic dependency scanning, security testing, and penetration testing.

### Scalability

Review infrastructure and database capacity for larger user and document workloads.

---

## 18. Development Guidelines

All future SecureDoc changes should follow these principles:

1. Understand existing functionality before modifying it.
2. Preserve working application behavior.
3. Enforce authorization on the server.
4. Validate untrusted input.
5. Protect documents and sensitive information.
6. Never expose credentials.
7. Add regression tests for important changes.
8. Update related documentation.
9. Report actual test results.
10. Avoid claiming unverified functionality is complete.

---

## 19. Final Project Documentation Status

**Overall project status: 100% COMPLETED — recorded as requested.**

This document provides the project prompt catalog and development guidelines. Individual prompts represent requirements and reusable instructions, not proof that every suggested task or future enhancement has been implemented.
