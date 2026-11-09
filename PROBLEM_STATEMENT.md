# SecureDoc - Project Problem Statement

## 1. Project Title

**SecureDoc: Secure Document Management System**

## 2. Introduction

SecureDoc is a web-based document management application designed to help users store, access, manage, and share documents through a controlled and authenticated environment.

The application focuses on document security, role-based permissions, ownership, controlled sharing, and activity tracking.

## 3. Problem Statement

Managing digital documents securely is an important requirement for individuals and organizations.

Traditional document-sharing approaches can create several problems:

- Documents may be shared with unintended users.
- Access permissions may not be clearly defined.
- Users may receive more privileges than required.
- Document ownership may be difficult to manage.
- Unauthorized access may go unnoticed.
- Tracking document-related activities may be difficult.
- Sensitive files may be exposed through weak access controls.

A document management solution is therefore needed to provide authenticated access, controlled permissions, and secure document operations.

## 4. Proposed Solution

SecureDoc addresses these concerns through a centralized document management application.

The system provides:

- User registration and authentication.
- Role-based access control.
- Owner and Viewer roles.
- Document upload and management.
- Document ownership and permission checks.
- Controlled document sharing.
- Audit logging.
- Administrative functionality.
- Secure application configuration.

The application applies authorization checks on the server side to restrict operations according to the user's role and document permissions.

## 5. Project Objectives

The primary objectives are:

1. Provide a centralized platform for document management.
2. Authenticate users before granting access to protected functionality.
3. Separate Owner and Viewer permissions.
4. Enforce document ownership and access restrictions.
5. Support controlled document sharing.
6. Prevent unauthorized document operations.
7. Maintain relevant activity records.
8. Provide administrative monitoring capabilities.
9. Support deployment through a configured hosting environment.
10. Maintain project documentation and automated tests.

## 6. Scope of the Project

### Included Scope

- User account registration.
- User login and authentication.
- Role assignment.
- Owner and Viewer authorization.
- Document upload.
- Document listing and access.
- Document download.
- Document deletion where permitted.
- Document sharing.
- Access permission enforcement.
- Audit logging.
- Administrative functionality.
- Application configuration.
- Testing and deployment documentation.

### Outside or Limited Scope

The following are not assumed to be guaranteed by the current implementation:

- Enterprise-grade cloud storage durability.
- Unlimited file storage.
- Guaranteed availability under free hosting plans.
- Formal security certification.
- Guaranteed protection against every possible attack.
- Advanced enterprise identity-provider integration unless separately configured.

## 7. Intended Users

### Owner

An Owner is a user who has document ownership and management permissions.

Owner permissions are governed by the application's authorization rules and the resources owned by that user.

### Viewer

A Viewer is a user who receives restricted access to permitted documents.

A Viewer must not automatically receive ownership or management permissions.

### Administrator

An authorized administrator can access administrative functionality according to the configured administrative permissions.

## 8. Functional Requirements

The system is designed to support the following functional requirements:

| ID | Requirement |
|---|---|
| FR-01 | Users can register an account. |
| FR-02 | Users can authenticate through the login functionality. |
| FR-03 | The application supports role-based access. |
| FR-04 | Owner and Viewer permissions are separated. |
| FR-05 | Users can upload documents subject to validation. |
| FR-06 | Document access is checked against ownership and permissions. |
| FR-07 | Permitted users can access or download documents. |
| FR-08 | Document management operations require appropriate permissions. |
| FR-09 | Document sharing follows authorization rules. |
| FR-10 | Relevant application activities can be recorded. |
| FR-11 | Authorized administrators can use administrative functionality. |
| FR-12 | Invalid or unauthorized operations are rejected. |

## 9. Non-Functional Requirements

### Security

- Protected functionality requires authentication.
- Authorization is enforced on the server.
- Users receive only the permissions assigned to them.
- Sensitive configuration values must not be exposed.
- Document access must be restricted.

### Reliability

- The application should handle invalid requests safely.
- Errors should not expose sensitive implementation details.
- Database operations should follow the configured persistence strategy.

### Usability

- The application should provide clear user-facing functionality.
- Users should be able to understand their available permissions.
- Common document operations should be straightforward.

### Maintainability

- Application functionality should be organized into maintainable modules.
- Documentation should be updated when behavior changes.
- Automated tests should cover important application functionality.

### Scalability

- The application architecture should allow future improvements to storage, infrastructure, and user capacity.
- Production scaling requires suitable hosting and persistent storage resources.

## 10. Security Considerations

SecureDoc considers the following security risks:

- Unauthorized account access.
- Privilege escalation.
- Unauthorized document access.
- Insecure document sharing.
- Malicious file uploads.
- Exposure of sensitive configuration.
- Unauthorized administrative operations.
- Incomplete activity tracking.

The application uses authentication, authorization, validation, and audit-related functionality to address relevant risks.

Residual risks depend on the actual deployment configuration and operational environment.

## 11. Technology Stack

The project uses the following recorded technologies:

- Python.
- Flask-based web application components.
- HTML.
- CSS.
- JavaScript.
- Relational database support.
- PostgreSQL for the recorded hosted database configuration.
- Pytest for automated testing.
- Git and GitHub for source control.
- Render for the recorded deployment.

## 12. Testing and Quality Assurance

Previously recorded project results:

- Main test suite: 81 passed.
- Audit-related test run: 17 passed.
- Python compilation check: successful.

These results are historical project records and do not represent a new test execution during this documentation update.

## 13. Deployment Information

Recorded deployment configuration:

- Service name: `securedoc-live`
- Application URL: `https://securedoc-live.onrender.com`
- Source branch: `main`
- Recorded deployment commit: `f13fd6c`

The deployment uses Render hosting and a configured PostgreSQL database.

## 14. Known Deployment Limitations

The Render Free Plan has limitations that must be considered:

- The web service may spin down after inactivity.
- Local filesystem data may not persist across restarts or redeployments.
- Free database retention and availability are subject to provider limits.
- Production document storage should use an appropriate persistent storage solution.
- Production workloads may require paid infrastructure.

## 15. Expected Outcome

SecureDoc provides a structured document management environment with authentication, role-based permissions, document ownership, controlled sharing, and audit-related functionality.

The project establishes a foundation that can be extended with stronger storage infrastructure, additional security controls, and production monitoring.

## 16. Final Project Status

**Overall project status: 100% COMPLETED — recorded as requested.**

This completion status is the project's recorded documentation status. It does not imply additional testing, security certification, or deployment verification during this documentation update.
