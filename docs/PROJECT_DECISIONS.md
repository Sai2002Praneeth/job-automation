# Project Decisions

## Architecture Decisions

The project follows a layered architecture.

API
↓
Service
↓
Repository
↓
Database

Each layer has a single responsibility.

Business logic must remain inside the Service Layer.

Repositories are responsible only for persistence.

Routers are responsible only for request validation and response handling.

Architecture changes should be avoided unless explicitly required.

---

## Database Decisions

PostgreSQL is the primary database.

SQLAlchemy 2.x ORM is used for database interaction.

Alembic manages all schema changes.

Schema modifications must never bypass Alembic.

Soft deletes should be preferred where practical instead of permanent deletion.

Database queries should remain inside repositories.

---

## Resume Decisions

Resume upload and resume parsing are independent operations.

Resume parsing must be reusable.

Resume parsing should support future features including:

- Resume tailoring
- ATS scoring
- Job matching
- Search profile generation

Uploaded resumes must never be overwritten.

Every significant resume update should create a new version.

Resume history must always be preserved.

---

## Search Decisions

The search engine must support multiple search profiles.

Search profiles may operate independently.

Job discovery should support:

- ATS platforms
- Job boards
- Company career sites

Experience filters should support:

- Automatic detection
- Manual override
- Ignore experience

Search results should be reusable across future workflows.

---

## Job Decisions

Every job must have a unique identity.

Duplicate jobs should never be stored.

Every job should store:

- Canonical Job URL
- Canonical Apply URL

Whenever possible, URLs should point directly to the exact job listing.

Expired jobs should remain in history but should no longer appear as active opportunities.

---

## AI Decisions

AI should assist decision making rather than replace user control.

Resume tailoring must never fabricate experience.

Cover letters should be generated from actual resume and job information.

Match scores should always be explainable.

Future AI providers should be replaceable without major architectural changes.

---

## Automation Decisions

Automation should prioritize reliability over aggressive behavior.

Auto Apply should never blindly submit every application.

Applications should pass through a Decision Engine.

Whenever automation cannot complete an application, the workflow should transition to Manual Action Required.

Failure reasons should always be recorded.

Browser automation should be modular and website-independent.

---

## Dashboard Decisions

Every discovered job must have a lifecycle state.

Jobs should never disappear silently.

The dashboard should present:

- Search status
- Match score
- Application status
- Resume version
- Cover letter availability
- Job source
- Canonical URLs
- Failure reasons when applicable

Application history should remain available.

---

## Analytics Decisions

The system should measure user outcomes instead of only automation activity.

Analytics should support:

- Resume performance
- Search profile performance
- Company response rates
- Application statistics
- Match score trends
- Skill gap analysis

Recommendations should be based on historical data whenever possible.

---

## Performance Decisions

Avoid duplicate work whenever possible.

Avoid duplicate searches.

Avoid duplicate applications.

Reuse previously processed data whenever practical.

Long-running operations should be designed to support asynchronous execution.

---

## Security Decisions

Secrets must never be stored in source code.

Uploaded files must be validated before processing.

Sensitive information should never appear in logs.

The principle of least privilege should be followed whenever possible.

---

## Future Reserved Decisions

Future architectural decisions should be recorded here instead of being scattered across implementation code or milestone prompts.

New permanent decisions should be added only after they become part of the agreed project architecture.

# Product Positioning

The application is an AI-assisted Job Search Operating System.

It is not an Auto Apply Bot.

Primary objectives:

- Find better jobs.
- Evaluate jobs intelligently.
- Automate repetitive work.
- Keep users in control.
- Preserve complete job-search history.

---

# Automation Strategy

Automation First

Human Assisted

Never Human Blocked

Automation should always be attempted when technically feasible.

If automation cannot continue:

- Save progress.
- Notify the user.
- Allow resuming from the failure point.

---

# Connector Architecture

All job portals must be implemented through a connector architecture.

Business logic must never depend on a specific portal implementation.

---

# Failure Recovery

Application failures are product features.

Failures should:

- be logged,
- be recoverable,
- appear in the Intervention Queue,
- never disappear silently.

## Resume Intelligence Strategy

The Resume Intelligence Engine will follow a modular pipeline.

Pipeline:

Resume PDF
    ↓
Structured Extraction
    ↓
Normalization
    ↓
Resume Intelligence
        ├── Resume Quality
        ├── ATS Compatibility
        ├── Keyword Coverage
        ├── GitHub Enrichment (optional)
        ├── Explainable Evaluation
        └── AI Suggestions

Implementation Notes

- The implementation may take architectural inspiration from open-source resume evaluation projects.
- External repositories should be treated as references rather than dependencies.
- Resume Intelligence must integrate with the existing Service → Repository → Database architecture.
- The evaluation pipeline must remain provider-agnostic.