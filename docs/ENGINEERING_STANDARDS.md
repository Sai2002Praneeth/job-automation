# Engineering Standards

## Project Philosophy

Write production-quality software.

Every implementation should prioritize:

- Readability
- Maintainability
- Reusability
- Simplicity
- Scalability
- Reliability

Prefer simple solutions over clever solutions.

Write code that another developer can easily understand and maintain.

---

## Architecture Principles

Follow the project architecture.

API Router
↓
Service Layer
↓
Repository Layer
↓
Database

Responsibilities must never leak across layers.

Business logic belongs only inside services.

Repositories are responsible only for database operations.

Routers are responsible only for request handling.

Never bypass layers unless explicitly instructed.

---

## General Coding Standards

Write clean, modular code.

Avoid duplicate implementations.

Keep functions focused on a single responsibility.

Keep classes cohesive.

Prefer composition over inheritance unless inheritance is clearly appropriate.

Avoid unnecessary abstractions.

Avoid premature optimization.

Never over-engineer a solution.

---

## Python Standards

Target Python 3.13.

Follow PEP 8.

Use meaningful names.

Use type hints whenever practical.

Use dataclasses when appropriate.

Use Enums instead of magic strings.

Avoid global mutable state.

Avoid deeply nested logic.

Prefer explicit code over implicit behavior.

---

## FastAPI Standards

Use FastAPI best practices.

Use dependency injection.

Keep routers thin.

Use response models.

Validate request models.

Raise appropriate HTTP exceptions.

Do not return raw database objects directly from routers.

---

## SQLAlchemy Standards

Use SQLAlchemy 2.x ORM.

Do not use raw SQL unless explicitly required.

Use relationships correctly.

Use transactions appropriately.

Do not duplicate queries across repositories.

Keep database access inside repositories.

Handle migrations using Alembic only.

Do not use Base.metadata.create_all() after Alembic has been introduced.

---

## Repository Standards

Repositories are responsible for persistence only.

Repositories should:

- accept a Session
- perform CRUD operations
- return ORM entities

Repositories must never contain business logic.

Repositories should not commit transactions unless explicitly required.

---

## Service Standards

Services contain all business logic.

Services should:

- coordinate repositories
- call utility modules
- orchestrate workflows
- remain reusable

Services must never depend on HTTP concepts.

Services should not access SQLAlchemy directly.

---

## API Standards

Routers should:

- validate requests
- call services
- return responses

Routers must never:

- implement business logic
- perform database queries
- duplicate validation already handled elsewhere

---

## Playwright Standards

Keep automation modular.

Separate browser management from website-specific logic.

Each supported website should have isolated automation.

Handle failures gracefully.

Always provide meaningful failure reasons.

Prefer resilient selectors over brittle implementations.

---

## Frontend Standards

Maintain reusable components.

Keep presentation separate from business logic.

Avoid duplicate UI components.

Use clear naming.

Keep pages lightweight.

---

## Configuration Standards

Store configuration in environment variables.

Never hardcode:

- passwords
- API keys
- database credentials
- secrets

Centralize configuration.

Avoid duplicated configuration values.

---

## Security Standards

Validate all external input.

Validate uploaded files.

Sanitize user-provided data where appropriate.

Never expose sensitive information.

Fail securely.

Follow the principle of least privilege.

---

## Logging Standards

Use structured logging.

Avoid print statements.

Log meaningful events.

Include sufficient information for debugging.

Never log secrets or sensitive information.

---

## Performance Standards

Avoid unnecessary work.

Avoid duplicate database queries.

Reuse existing services.

Prefer efficient algorithms when practical.

Optimize only after correctness.

---

## Error Handling Standards

Handle expected errors gracefully.

Return meaningful error messages.

Do not silently ignore exceptions.

Provide actionable error information where appropriate.

---

## Documentation Standards

Write self-explanatory code first.

Document public classes and public functions when needed.

Keep comments focused on explaining "why", not "what".

Remove outdated comments.

---

## Testing Standards

Every implementation should be verified before completion.

Confirm:

- imports are correct
- syntax is valid
- application starts successfully
- existing functionality remains intact
- new functionality behaves correctly

Prevent regressions.

---

## Code Review Checklist

Before considering a task complete:

- Remove unused imports.
- Remove unused variables.
- Remove dead code.
- Remove commented-out code.
- Remove duplicate logic.
- Verify naming consistency.
- Verify project structure.
- Verify backward compatibility.
- Verify error handling.
- Verify configuration.
- Verify readability.

---

## Definition of Done

A task is complete only if:

- Requirements are fully implemented.
- Acceptance criteria are satisfied.
- Code follows project architecture.
- Code follows engineering standards.
- Existing functionality remains unaffected.
- Application starts successfully.
- No unnecessary files were modified.
- Modified files are reported.