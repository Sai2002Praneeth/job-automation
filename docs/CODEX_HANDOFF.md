# Codex Handoff

## Current Architecture

The backend follows the required layered architecture:

API Router -> Service Layer -> Repository Layer -> Database/File System

Routers validate HTTP requests and return response models. Services own reusable business rules. Repositories are the only SQLAlchemy layer. Resume and job-description intelligence are deterministic and independent of persistence workflows.

## Completed Milestones

- M1â€“M11: Resume upload, parsing, persistence, versioning, library, and management
- M12: Resume Intelligence Core
- M13: Job Description Intelligence

## Current Milestone

M13 â€” Job Description Intelligence is complete, including its response-model regression fix.

## Newly Implemented Features

- Deterministic, request-scoped job profile extraction.
- Required and preferred technology skill extraction, using the shared M12 normalization utility.
- Experience, education, location/work arrangement, salary, employment-type, and responsibility extraction.
- Content statistics and explainable job-description quality warnings.
- Regression fix: quality warning service dataclasses are now explicitly translated to the declared nested Pydantic response model before serialization.
- No AI, LLM, external service, or persistence is used.

## Database Changes

None. Job descriptions are not persisted, and no Alembic migration was added.

## API Changes

The following endpoints accept a JSON body with `description` and optional `title`:

- `POST /api/job/analyze`
- `POST /api/job/profile`
- `POST /api/job/statistics`
- `POST /api/job/quality`

All operations are published in OpenAPI. Existing API behavior remains unchanged.

## Files/Modules Added

- `backend/services/job_description_intelligence_service.py`
- `backend/api/job.py`
- `backend/tests/test_job_description_intelligence.py`

M13 also updates `backend/main.py` to register the router and `backend/models/response.py` with request and response models.

## Important Implementation Decisions

- `JobDescriptionIntelligenceService` contains all parsing, normalization, statistics, and warning rules; it has no HTTP, repository, or SQLAlchemy dependency.
- Technology aliases are canonicalized through `utils.skill_normalization.normalize_skills`, shared with M12.
- Qualification section markers make bullet items inherit Required or Preferred classification.
- Rules are intentionally explicit and explainable; the technology vocabulary can be expanded through reviewed deterministic additions.

## Pending Milestones

- Job matching and skill-gap analysis using resume and job intelligence
- Resume tailoring, cover-letter generation, and decision workflows
- Job connector, validation/deduplication, automation, tracking, and dashboard milestones

## Known Limitations

- Extraction is heuristic and supports common English headings and formats only.
- Location, salary, education field, and experience parsing are conservative rather than exhaustive.
- Job descriptions are analyzed only per request and cannot yet be retrieved later.
- Real HTTP integration tests run a temporary Uvicorn server using the standard library because this environment does not include `httpx` for FastAPI `TestClient`.

## Recommended Starting Point for the Next Codex Session

Build the agreed resume-to-job matching or skill-gap workflow by composing `ResumeIntelligenceService` and `JobDescriptionIntelligenceService`. Keep it deterministic unless a future approved milestone explicitly adds a replaceable AI provider.
