# Codex Handoff

## Current Architecture

The backend follows the required layered architecture:

API Router -> Service Layer -> Repository Layer -> Database/File System

Routers handle HTTP validation and responses. Services own business rules. Repositories are the only layer that uses SQLAlchemy. Resume parsing remains independent of upload and reusable by future workflows.

## Completed Milestones

- M1 FastAPI Setup through M8 Resume Persistence
- M9 Resume Versioning
- M10 Resume Library
- M11 Resume Management
- M12 Resume Intelligence Core

## Current Milestone

M12 Resume Intelligence Core is complete. Existing resume upload, parsing, versioning, library, and download behavior remains compatible.

## Newly Implemented Features

- Deterministic Resume Profile generation from persisted parsed data.
- Skill canonicalization with alias handling and duplicate removal.
- Detection of summary, skills, experience, education, projects, and certifications sections.
- Explainable completeness assessment for contact fields and core sections.
- Resume statistics: word, character, line, skill, duplicate-skill, and detected-section counts.
- Rule-based quality warnings for missing core data, short resume text, and duplicate skills.
- Automated regression coverage for intelligence behavior and missing resumes.

## Database Changes

No schema changes were required and no Alembic migration was added. Resume Intelligence is read-only and derives results from existing `resumes` fields, especially `raw_text`, contact data, skills, education, experience, and projects.

## API Changes

New endpoints:

- `GET /api/resume/{id}/profile`
- `GET /api/resume/{id}/statistics`
- `GET /api/resume/{id}/quality`
- `GET /api/resume/{id}/normalized-skills`

All return `404` for a nonexistent resume version. Existing endpoints are unchanged. Response models make the new operations available in generated OpenAPI documentation.

## Files/Modules Added

- `backend/services/resume_intelligence_service.py`
- `backend/tests/test_resume_intelligence.py`

M12 also updates `backend/api/resume.py`, `backend/models/response.py`, and this handoff.

## Important Implementation Decisions

- `ResumeIntelligenceService` contains all deterministic intelligence rules and calls `ResumeService`; it does not access SQLAlchemy or HTTP concerns.
- Results reuse persisted parsed resume data and are never written back to the database.
- No AI, LLM, external service, or new dependency is involved.
- Skill normalization is deliberately explainable through a small canonical alias map rather than probabilistic matching.
- Quality warnings report specific, actionable reasons rather than opaque scores.

## Pending Milestones

- M13 Connector Framework
- M14 Greenhouse Connector
- M15 Lever Connector
- M16 Ashby Connector
- M17 Company Career Connector
- M18 Job Board Connector
- M19 Job Normalization
- M20 Duplicate Detection
- M21 Job Health Monitor

## Known Limitations

- Resume ownership remains global/single-user because accounts are not implemented.
- Resume management and intelligence are backend APIs only; there is no frontend UI.
- Section detection relies on recognized headings and existing parser output; unconventional formatting may not be detected.
- Skill aliases are intentionally limited and should be expanded only through reviewed deterministic rules.
- Resume Intelligence does not yet evaluate a resume against a job description.

## Recommended Starting Point for the Next Codex Session

Start the agreed next milestone, retaining the API -> Service -> Repository architecture. Keep the Resume Intelligence service deterministic and read-only unless a future approved milestone explicitly introduces provider-backed evaluation.
