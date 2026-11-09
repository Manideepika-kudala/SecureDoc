# SecureDoc API Documentation

## 1. Overview

SecureDoc is a secure document management application designed to support authenticated access, role-based authorization, document operations, controlled sharing, and audit logging.

This document describes the API capabilities and expected behavior at a functional level.

For the exact registered routes, HTTP methods, request schemas, and response schemas, use the application's generated OpenAPI specification.

## 2. API Documentation and Specification

When the application is running, check the following locations:

- OpenAPI specification: `/openapi.json`
- Swagger UI: `/docs`
- ReDoc: `/redoc`

Availability of interactive documentation depends on the application configuration.

The generated OpenAPI specification is the authoritative reference for actual endpoint paths and schemas.

## 3. Authentication and Account Management

The authentication module supports account-related operations.

Main responsibilities:

- User registration.
- User login.
- Authentication and session handling.
- Logout.
- Access to authenticated application features.
- Account identity management.

Protected operations require a valid authenticated session or the authentication mechanism configured by the application.

Authentication failures should not grant access to protected resources.

## 4. Role-Based Access Control

SecureDoc uses role-based authorization.

### Owner

The Owner role is intended for users who need document ownership and management permissions.

Depending on the resource and configured authorization rules, Owner capabilities include:

- Managing owned documents.
- Accessing permitted document operations.
- Managing document sharing.
- Controlling access granted to other users.
- Performing operations allowed by ownership rules.

### Viewer

The Viewer role is intended for users who need restricted document access.

Viewer capabilities are limited to operations explicitly permitted by the authorization rules.

A Viewer must not receive Owner-only permissions simply because the user is authenticated.

### Authorization Rules

- Authentication and authorization are separate checks.
- Every protected operation must enforce the relevant permission.
- Document ownership and sharing permissions must be considered.
- Unauthorized operations must be rejected.
- Role restrictions must be enforced on the server, not only in the user interface.

## 5. Document Management

The document module provides the application's document-related functionality.

Supported functional areas include:

- Document upload.
- Document listing and access.
- Document details.
- Document download.
- Document deletion where permitted.
- Document sharing and access management.
- Document ownership and permission enforcement.

Document operations must validate the authenticated user and the permissions associated with the requested document.

The application should not expose private documents to users without authorization.

## 6. Document Sharing

Document sharing allows access to be granted according to the application's sharing and authorization rules.

Important considerations:

- Only permitted users can manage sharing.
- Shared access must be associated with the relevant document and user.
- Viewer access must remain restricted.
- Ownership permissions must not be unintentionally transferred.
- Revoked access must no longer authorize protected operations.

## 7. Audit Logging

The audit functionality records relevant application activities.

Audit-related responsibilities include:

- Recording important user actions.
- Maintaining activity history.
- Supporting administrative review.
- Helping investigate unauthorized or unexpected operations.

Audit records should be protected from unauthorized modification and access.

## 8. Administrative Functionality

Administrative functionality is intended for authorized administrative users.

Depending on the configured application permissions, administrative capabilities may include:

- User and account administration.
- Reviewing application activity.
- Accessing audit information.
- Monitoring application operations.

Administrative operations must enforce the configured administrative authorization rules.

## 9. Request and Response Behavior

API requests should use the HTTP methods and request formats defined in the generated OpenAPI specification.

General behavior:

- Successful requests return the response defined by the endpoint.
- Invalid input should produce an appropriate validation response.
- Unauthenticated requests to protected resources should be rejected.
- Authenticated users without sufficient permissions should be denied.
- Missing resources should return an appropriate not-found response.
- Unexpected server errors should not expose secret values or internal implementation details.

## 10. Security Requirements

The API security model includes the following principles:

- Authentication before protected access.
- Server-side authorization.
- Role-based access restrictions.
- Document ownership checks.
- Permission checks for shared documents.
- Secure handling of uploaded files.
- Protection of sensitive configuration values.
- Audit logging for relevant operations.
- Safe error responses.

## 11. Configuration

The application uses environment-based configuration for sensitive and deployment-specific values.

Do not place secret keys, database passwords, or other credentials directly in source code or public documentation.

Configure the required environment variables according to the project's deployment and application configuration.

## 12. Testing

API-related tests should cover:

- Authentication behavior.
- Registration and login validation.
- Role-based access restrictions.
- Document authorization.
- Document sharing permissions.
- Administrative authorization.
- Audit functionality.
- Invalid request handling.
- Unauthorized access attempts.

Previously recorded project test result:

- Main test suite: 81 passed.
- Audit-related test run: 17 passed.
- Python compilation check: successful.

These are previously recorded results, not a new test execution performed while writing this document.

## 13. Deployment

Recorded deployment information:

- Service: `securedoc-live`
- Application URL: `https://securedoc-live.onrender.com`
- Git branch: `main`
- Recorded deployment commit: `f13fd6c`

Deployment configuration and current application behavior should be checked in the hosting dashboard when operational confirmation is required.

## 14. Deployment Limitations

The Render Free Plan has operational limitations.

Important considerations:

- Free web services may spin down after inactivity.
- Local filesystem changes may not persist across service restarts or redeployments.
- Free database availability and retention are subject to provider limits.
- File storage should use persistent storage for production requirements.
- Required external dependencies must be installed in the deployment environment.

## 15. API Maintenance

When API functionality changes:

1. Update the relevant route implementation.
2. Update request and response validation.
3. Update authorization checks.
4. Add or update automated tests.
5. Confirm the generated OpenAPI specification.
6. Update this documentation when behavior changes.

---

## Final Project Documentation Status

**Project status: 100% COMPLETED — recorded as requested.**

This document describes the API capabilities at a functional level. The generated OpenAPI specification remains the source of truth for exact endpoint definitions.
