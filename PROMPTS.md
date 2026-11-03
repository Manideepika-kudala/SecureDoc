# SecureDoc - AI Prompt Log

## Purpose
This file records AI-assisted development during the Snovasys Fresher Hiring Challenge.

Entries will be updated as prompts are actually used, outputs are reviewed, and fixes are committed.

## Day 1 - November 3, 2026

### Entry 1 - Project Requirements and Planning

*Prompt used:*
I have the Snovasys Fresher Hiring Challenge problem statement. Help me break it into a seven-day implementation plan for SecureDoc. Include all functional requirements, security requirements, documentation, tests, deployment, and submission deliverables. Do not mark features complete before implementation and verification.

*Expected output:*
A structured roadmap and project documentation outline.

*Review:*
The roadmap must be checked against the original challenge statement to ensure that no requirements are omitted.

*Correction:*
Any missing requirements will be added manually and reflected in the implementation plan.

*Commit reference:*
To be added after the corresponding commit is created.

### Entry 2 - Threat Model

*Prompt used:*
Help me identify realistic security threats for a document-sharing application. Consider IDOR, unauthorized downloads, permission revocation, file upload validation, audit log tampering, search information leakage, and excessive privileges. For each threat, describe a mitigation and a test that could verify it. Do not claim the mitigation is implemented unless code and tests prove it.

*Expected output:*
A threat list with mitigations and verification ideas.

*Review:*
Threat descriptions and proposed mitigations must be validated against the actual architecture and implementation.

*Correction:*
Implementation-specific weaknesses and accepted trade-offs will be documented as the project progresses.

*Commit reference:*
To be added after the corresponding commit is created.

## Reusable AI Instructions

- Do not invent completed work, test results, or deployment status.
- Prioritize server-side authorization and data confidentiality.
- Explain security-sensitive code before proposing it.
- Identify assumptions and potential failure cases.
- Require human review of AI-generated permission suggestions.
