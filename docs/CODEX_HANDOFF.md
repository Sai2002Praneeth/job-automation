# Codex Handoff

## Current Architecture

The backend follows the project-standard layered architecture:

API Router -> Service Layer -> Repository Layer -> Database/File System

FastAPI routers validate requests and call services. Services own business workflows. Repositories contain SQLAlchemy persistence only. Resume parsing remains independent from upload and persistence so future modules can reuse it.

## Completed Milestones

- M1 FastAPI Setup
- M2 Resume Upload
- M3 Resume Parser
- M3.5 Resume Processing Pipeline
- M4 Database Infrastructure
- M5 Database Models
- M6 Alembic Migration
- M7 Repository Layer
- M8 Resume Persistence
- M9 Resume Versioning
- M10 Resume Library

## Current Milestone

M10 - Resume Library is implemented and verified. The system now supports multiple named resume library entries, each with independent version history and exactly one active version.

## Newly Implemented Features

- Added named resume library entries such as Java Resume, Backend Resume, and ML Resume.
- Each library entry owns its own resume versions.
- Active version state is scoped per library entry.
- Existing file-only resume upload remains functional and appends to the currently active library when no library is specified.
- Resume upload can target an existing library by `resume_library_id`.
- Resume upload can create or reuse a library by `resume_library_name`.
- Added APIs to list libraries, list versions for a library, and fetch a library's active version.

## Database Changes

- Added `resume_libraries` table with `id`, `name`, `created_at`, and `updated_at`.
- Added `resumes.resume_library_id` foreign key to `resume_libraries.id`.
- Added unique library name index.
- Added unique constraint for `(resume_library_id, version_number)`.
- Added partial unique index to enforce one active version per library.
- Backfilled existing resume histories into library entries in migration `b2c4d6e8f0a1_add_resume_library.py`.
- Preserved legacy `root_resume_id` for backward-compatible version history behavior.

## API Changes

- `POST /api/resume/upload` now accepts optional multipart form fields:
  - `resume_library_id`
  - `resume_library_name`
- Upload responses now include:
  - `resume_library_id`
  - `resume_library_name`
- Added `GET /api/resume/libraries`.
- Added `GET /api/resume/libraries/{resume_library_id}/versions`.
- Added `GET /api/resume/libraries/{resume_library_id}/active`.
- Existing `POST /api/resume/parse` behavior is preserved.

## Files/Modules Added

- `backend/alembic/versions/b2c4d6e8f0a1_add_resume_library.py`
- `ResumeLibrary` ORM model in `backend/models/resume.py`
- Resume library response models in `backend/models/response.py`

## Important Implementation Decisions

- `ResumeLibrary` is the parent object for independent resume histories.
- `Resume` remains the version record used by applications and parsing workflows.
- Version activation is handled in `ResumeService`, not repositories or routers.
- Repositories remain limited to persistence operations and SQLAlchemy queries.
- `root_resume_id` remains in place for compatibility, while `resume_library_id` is the new boundary for independent histories.
- File-only uploads keep backward compatibility by using the current active library when available, or creating a default library from the uploaded filename.

## Pending Milestones

- M11 Resume Performance Analytics
- M12 Search Profile Engine
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

- No endpoint exists yet to rename or delete a resume library entry.
- No endpoint exists yet to manually switch the active version; active version changes when a new version is uploaded to a library.
- Library ownership is single-user/global because user accounts are not implemented yet.
- Resume Library has backend support only; no frontend UI is implemented yet.
- Existing applications still reference a specific `Resume` version, which is correct, but application-facing library views are not yet built.

## Recommended Starting Point for Next Codex Session

Start with M11 - Resume Performance Analytics. Read `AGENTS.md`, `docs/ENGINEERING_STANDARDS.md`, `docs/PROJECT_ROADMAP.md`, `docs/PROJECT_DECISIONS.md`, and `docs/PRODUCT_REQUIREMENTS.md` first. Then inspect the current resume library/version model and application model to design analytics around application outcomes per resume library and per resume version.
