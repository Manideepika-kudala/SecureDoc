# SecureDoc - Implementation Plan

## 7-Day Roadmap

### Day 1 - Threat Modeling and Data Architecture
- Understand the Snovasys challenge requirements.
- Define Admin, Owner, and Viewer roles.
- Design per-document READ and EDIT permissions.
- Identify security threats and mitigations.
- Design database schema and repository documentation.
- Commit and push Day 1 progress.

### Day 2 - Authentication and Secure Storage
- Implement user registration/login and authentication.
- Configure password hashing and session/token security.
- Implement private document storage.
- Validate uploaded file types, signatures, and size.
- Implement document ownership management.
- Record AI prompts and implementation review.

### Day 3 - Authorization and Instant Revocation
- Implement centralized server-side authorization.
- Enforce per-document permissions on every document endpoint.
- Implement secure document downloads.
- Implement permission grant and revocation.
- Ensure revoked access is rejected immediately.
- Add authorization-focused tests.

### Day 4 - Audit Trail and Admin Dashboard
- Implement append-only audit records.
- Record successful and denied document access.
- Record uploads, downloads, changes, deletions, and permission changes.
- Implement administrative activity views.
- Add optional AI permission suggestions requiring owner approval.

### Day 5 - Search, Validation, and Deployment
- Implement secure document search.
- Filter search results using authorization rules.
- Harden input validation and file handling.
- Deploy the application and database.
- Verify deployed authentication and document access.
- Document deployment and configuration.

### Day 6 - Automated Security Testing
- Test unauthorized document access.
- Test revoked permission behavior.
- Test unauthenticated direct file access.
- Test token/session revocation.
- Test audit records for denied attempts.
- Perform authorization mutant test.
- Fix discovered security issues.

### Day 7 - Final Validation and Submission
- Verify live deployment and seeded accounts.
- Review security and functionality requirements.
- Finalize THREATS.md, PROMPTS.md, README.md, and API.md.
- Verify Git history and repository contents.
- Record five-minute demo video.
- Prepare final project write-up and submission.

## Engineering Principles
- Server-side authorization is mandatory.
- Never trust frontend permission checks.
- Store documents privately.
- Re-check authorization before every document operation.
- Record security-relevant actions.
- Document limitations honestly.
