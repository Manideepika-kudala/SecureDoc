# SecureDoc - Database Architecture

## Purpose
Design a relational database for secure document sharing, permissions, and audit records.

## Tables

### Users
- Id: Primary key
- Email: Unique, required
- PasswordHash: Required
- Role: ADMIN, OWNER, or VIEWER
- RevokedTokensBefore: Token revocation timestamp
- CreatedAt: Account creation timestamp

### Documents
- Id: Primary key
- Title: Required
- OwnerId: Foreign key to Users
- FileKey: Random private storage identifier
- ContentHash: File integrity hash
- Category: Document category
- CreatedAt: Upload timestamp

### Permissions
- Id: Primary key
- DocumentId: Foreign key to Documents
- UserId: Foreign key to Users
- Level: READ or EDIT
- GrantedBy: Foreign key to Users
- CreatedAt: Permission creation timestamp
- ExpiresAt: Optional permission expiry timestamp

### AuditLogs
- Id: Primary key
- Timestamp: Event timestamp
- Action: Event type
- ActorId: User who performed the action
- TargetDocumentId: Optional document reference
- Status: SUCCESS or DENIED
- IPAddress: Request IP address
- UserAgent: Request user agent
- PreviousState: Optional prior state
- NewState: Optional new state

## Relationships
- One user can own many documents.
- One document can have multiple permission grants.
- One user can receive permissions to multiple documents.
- Audit records identify the actor and target document when applicable.

## Security Constraints
- Emails must be unique.
- Foreign keys must be enforced.
- Permission levels must be constrained to READ and EDIT.
- Roles must be constrained to ADMIN, OWNER, and VIEWER.
- Audit logs must be append-only.
- Documents must reference private storage keys, not public URLs.
- Document access decisions must use current database permissions.

## Permission Model
- Owners manage their own documents.
- Viewers can access only documents explicitly shared with them.
- READ grants viewing and downloading.
- EDIT grants reading and permitted document changes.
- Administrators can view system activity but do not automatically bypass document authorization.

## Design Note
This is the planned logical schema. The final database engine and migration syntax will be selected during implementation.

## Finalized Design Decisions

### Permission Model
- Document-level permissions are granted to named users.
- READ allows viewing and downloading.
- EDIT allows reading and modifying permitted document content.
- Owners manage permissions for their own documents.
- Administrators can view system activity but do not automatically bypass document authorization.
- Permissions may have an optional expiry timestamp.

### Document Storage
- Uploaded files are stored using random storage keys.
- Original filenames are treated as metadata only.
- Files are not served from a public directory.
- Download requests must pass server-side authorization.

### Access Revocation
- Permissions are updated in the database immediately.
- Every document request checks current authorization.
- Long-lived permission caches are avoided.
- Any issued download URL must have a short expiry and documented revocation limitation.

### Audit Trail
- Security-relevant actions are recorded.
- Successful and denied access attempts are recorded.
- Audit records are append-only.
- Database permissions and integrity controls will protect audit records.

### Search
- Search results are filtered using the requesting user's authorization.
- Unauthorized document metadata must not be exposed.
- Search supports document title, owner, category, and date.

### Known Limitations
- The current schema is a design draft, not a deployed database.
- Database-specific constraints and append-only enforcement will be verified during implementation.
- Storage security and authorization behavior require automated tests.
