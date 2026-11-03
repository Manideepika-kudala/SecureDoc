-- SecureDoc Database Schema
-- Day 1: Initial logical database architecture

CREATE TABLE Users (
    Id VARCHAR(36) PRIMARY KEY,
    Email VARCHAR(255) NOT NULL UNIQUE,
    PasswordHash VARCHAR(255) NOT NULL,
    Role VARCHAR(20) NOT NULL
        CHECK (Role IN ('ADMIN', 'OWNER', 'VIEWER')),
    RevokedTokensBefore TIMESTAMP NULL,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Documents (
    Id VARCHAR(36) PRIMARY KEY,
    Title VARCHAR(255) NOT NULL,
    OwnerId VARCHAR(36) NOT NULL,
    FileKey VARCHAR(255) NOT NULL UNIQUE,
    ContentHash VARCHAR(128) NOT NULL,
    Category VARCHAR(100),
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (OwnerId) REFERENCES Users(Id)
);

CREATE TABLE Permissions (
    Id VARCHAR(36) PRIMARY KEY,
    DocumentId VARCHAR(36) NOT NULL,
    UserId VARCHAR(36) NOT NULL,
    Level VARCHAR(10) NOT NULL
        CHECK (Level IN ('READ', 'EDIT')),
    GrantedBy VARCHAR(36) NOT NULL,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt TIMESTAMP NULL,
    FOREIGN KEY (DocumentId) REFERENCES Documents(Id),
    FOREIGN KEY (UserId) REFERENCES Users(Id),
    FOREIGN KEY (GrantedBy) REFERENCES Users(Id),
    UNIQUE (DocumentId, UserId)
);

CREATE TABLE AuditLogs (
    Id VARCHAR(36) PRIMARY KEY,
    Timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    Action VARCHAR(100) NOT NULL,
    ActorId VARCHAR(36),
    TargetDocumentId VARCHAR(36),
    Status VARCHAR(10) NOT NULL
        CHECK (Status IN ('SUCCESS', 'DENIED')),
    IPAddress VARCHAR(45),
    UserAgent VARCHAR(500),
    PreviousState TEXT,
    NewState TEXT,
    FOREIGN KEY (ActorId) REFERENCES Users(Id),
    FOREIGN KEY (TargetDocumentId) REFERENCES Documents(Id)
);

CREATE INDEX idx_documents_owner
    ON Documents(OwnerId);

CREATE INDEX idx_permissions_user_document
    ON Permissions(UserId, DocumentId);

CREATE INDEX idx_audit_timestamp
    ON AuditLogs(Timestamp);

CREATE INDEX idx_audit_actor
    ON AuditLogs(ActorId);

-- IMPORTANT:
-- This is an initial schema draft.
-- Append-only audit enforcement, authorization logic,
-- and database-specific migration behavior must be implemented
-- and verified during later development days.
