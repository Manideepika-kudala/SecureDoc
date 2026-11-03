# SecureDoc - Problem Statement

## Snovasys Fresher Hiring Challenge 2026

*Challenge:* TrustVault — Secure Document Sharing with a Real Audit Trail

*Project Name:* SecureDoc

*Duration:* November 1–7, 2026

## Problem

Organizations share confidential documents with employees, customers, and external partners. Unauthorized access, excessive permissions, and missing audit evidence create security and compliance risks.

SecureDoc aims to build a secure document-sharing platform where only explicitly authorized users can access documents and every important action is recorded in a tamper-resistant audit trail.

## Functional Requirements

1. Authentication with Admin, Owner, and Viewer roles.
2. Upload, organize, search, and manage documents.
3. Grant per-document READ and EDIT permissions to named users.
4. Owners can grant and revoke document access.
5. Unauthorized users cannot read, download, modify, or delete documents.
6. Audit uploads, downloads, changes, deletions, and permission changes.
7. Search by document name, owner, category, and date.
8. Validate uploaded files.
9. Provide an administrative activity and permission-change view.
10. Automated security tests proving users cannot access documents without authorization.

## Security Requirements

- Server-side authorization for every document operation.
- Secure file storage inaccessible through direct public URLs.
- Immediate access revocation.
- Append-only audit trail.
- Protection against IDOR and unauthorized document access.
- Honest threat documentation and security test evidence.

## Deliverables

- Public Git repository with daily commit history.
- Live deployment with seeded accounts.
- THREATS.md and PROMPTS.md.
- Automated tests.
- Database schema and setup scripts.
- API documentation.
- Five-minute demo video.
- Project write-up.
