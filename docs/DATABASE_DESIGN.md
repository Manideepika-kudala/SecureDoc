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
