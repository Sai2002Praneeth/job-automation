# AGENTS

## Project Overview

This repository contains an AI-powered Job Automation Platform that helps users search for jobs, analyze resumes, tailor resumes, generate cover letters, automate job applications where possible, and track application progress.

The primary objective is to build a production-quality, modular, maintainable, and scalable application.

---

## Tech Stack

- Python 3.13
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Playwright
- TypeScript
- React (future)
- VS Code

---

## High-Level Architecture

Always follow the project architecture.

```
API Router
    ↓
Service Layer
    ↓
Repository Layer
    ↓
Database / File System
```

Never bypass layers unless explicitly instructed.

---

## Project Structure

```
backend/
    api/
    services/
    repositories/
    models/
    database/
    utils/

automation/
    playwright/
    sites/
    pages/

frontend/

resume/

generated/
```

Follow the existing project structure.

Create new folders only when they provide clear architectural value.

---

## Layer Responsibilities

### API Layer

API routers are responsible only for:

- Receiving requests
- Validating requests
- Calling services
- Returning responses

API routers must never contain business logic or database logic.

---

### Service Layer

Services are responsible for business logic.

Services should:

- be reusable
- remain independent of API routers
- coordinate repositories and utility modules
- contain feature-specific workflows

Services must never depend on HTTP-specific behavior.

---

### Repository Layer

Repositories are the only layer allowed to communicate directly with SQLAlchemy ORM.

Repositories should:

- receive a SQLAlchemy Session
- perform CRUD operations
- return ORM entities

Repositories must not contain business logic.

Repositories must not commit transactions unless explicitly required.

---

### Database Layer

Database models represent persistent data only.

Database models should not contain business logic.

Schema changes must be handled through Alembic migrations.

---

## Service Design Rules

When functionality may be reused by multiple features, implement it as a reusable service instead of embedding the logic inside a specific feature.

Prefer extending existing services over creating duplicate implementations.

Keep services cohesive and focused on a single responsibility.

---

## Resume Processing Rules

Resume parsing must remain independent of uploading.

The parser should be reusable by future modules including:

- Resume Upload
- Resume Tailoring
- ATS Scoring
- Job Matching
- Search Profile Generation

Do not tightly couple parsing logic to any specific API endpoint.

---

## Dependency Rules

Prefer existing project modules before introducing new dependencies.

Do not install additional libraries unless they provide significant value that cannot reasonably be implemented using the current stack.

---

## Security Rules

Validate all external input.

Validate uploaded files before processing.

Never expose secrets.

Never hardcode credentials.

Always load configuration from environment variables.

---

## Configuration Rules

Application configuration must come from `.env`.

Do not duplicate configuration values across the project.

Keep configuration centralized.

---

## Workflow Rules

For every requested task:

- Implement only the requested feature.
- Preserve backward compatibility.
- Minimize unrelated modifications.
- Reuse existing architecture whenever possible.
- Avoid unnecessary refactoring.
- Keep the implementation consistent with existing project structure.

---

## Commands

### Run Backend

```
cd backend
uvicorn main:app --reload
```

### Database Migration

```
alembic revision --autogenerate -m "<message>"
alembic upgrade head
```

### Current Migration

```
alembic current
```

---

## AI Agent Rules

Always read and follow:

- ENGINEERING_STANDARDS.md
- PROJECT_ROADMAP.md
- PROJECT_DECISIONS.md
- PRODUCT_REQUIREMENTS.md

Before finishing any task:

- Verify imports.
- Verify syntax.
- Ensure the application starts successfully.
- Preserve existing functionality.
- Report only modified files.

Do not:

- modify unrelated files
- perform Git operations
- change project architecture without instruction
- introduce breaking changes

## Extensibility

The system must remain modular and extensible.

Rules:

- Every external job source must be implemented as a connector.
- Never place portal-specific logic inside services.
- New connectors must implement the common connector interface.
- AI providers should remain replaceable.
- Keep automation independent of any specific ATS or job board.
- Reuse existing abstractions whenever possible.
- Avoid creating duplicate implementations.