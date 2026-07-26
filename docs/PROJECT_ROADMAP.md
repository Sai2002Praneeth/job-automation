# Project Roadmap

## Product Vision

Build an AI-powered Job Automation Platform that helps users discover relevant jobs, optimize resumes, automate job applications where appropriate, and track the complete job application lifecycle from job discovery to offer.

The platform should prioritize reliability, scalability, maintainability, and user control over blind automation.

---

## Final Goal

Deliver a production-quality platform capable of:

- Managing resumes
- Building intelligent search profiles
- Discovering jobs from multiple sources
- Matching resumes against job descriptions
- Tailoring resumes
- Generating cover letters
- Automating applications where technically feasible
- Providing manual assistance where automation is not possible
- Tracking every application
- Providing actionable analytics and recommendations

---

## Architecture Overview

The application follows a layered architecture.

```
API
    ↓
Service
    ↓
Repository
    ↓
Database
```

The product consists of several major modules that will be implemented incrementally throughout the project.

---

## Phase 1 — Foundation

Goal

Build the project foundation and establish a scalable backend architecture.

Milestones

- M1 FastAPI Setup
- M2 Resume Upload
- M3 Resume Parser
- M3.5 Resume Processing Pipeline
- M4 Database Infrastructure
- M5 Database Models
- M6 Alembic Migration

Status

Completed

---

## Phase 2 — Data Layer

Goal

Create a reusable persistence layer that separates business logic from database access.

Milestones

- M7 Repository Layer
- M8 Resume Persistence
- M9 Resume Versioning

Status

In Progress

---

## Phase 3 — Intelligent Job Discovery

Goal

Build an intelligent search engine capable of discovering jobs from multiple sources.

Milestones

- M10 Search Profile Engine
- M11 Greenhouse Integration
- M12 Lever Integration
- M13 Ashby Integration
- M14 Company Career Discovery
- M15 Job Board Integration
- M16 Unified Search Service
- M17 Validation and Deduplication

Status

Planned

---

## Phase 4 — AI Intelligence

Goal

Use AI to improve resume quality and application success.

Milestones

- M18 Job Description Parser
- M19 Resume Match Engine
- M20 Resume Tailoring
- M21 Cover Letter Generation
- M22 Decision Engine

Status

Planned

---

## Phase 5 — Automation

Goal

Automate job applications where possible while maintaining safe manual fallbacks.

Milestones

- M23 Playwright Session Manager
- M24 Auto Apply Engine
- M25 Manual Action Workflow
- M26 Application Tracking

Status

Planned

---

## Phase 6 — Dashboard and Analytics

Goal

Provide complete visibility into job searches, applications, and performance.

Milestones

- M27 Dashboard
- M28 Analytics
- M29 Notifications
- M30 Production Readiness

Status

Planned

---

## Current Milestone

M7 — Repository Layer

Current focus:

- Implement reusable repositories.
- Separate persistence from business logic.
- Preserve existing API behavior.

---

## Completed Milestones

- M1 FastAPI Setup
- M2 Resume Upload
- M3 Resume Parser
- M3.5 Resume Processing Pipeline
- M4 Database Infrastructure
- M5 Database Models
- M6 Alembic Migration

---

## Future Milestones

Future enhancements may be added after M30.

Possible examples include:

- AI interview preparation
- Resume quality benchmarking
- Referral management
- Browser extension
- Mobile application
- Multi-user support

These enhancements are intentionally outside the initial roadmap and should not affect the current implementation plan.

# Current Status

Current Phase

Phase 2 — Resume Management

Current Milestone

M9 — Resume Versioning

Completed

M1–M8

---

# Phase 1 — Foundation ✅

- M1 FastAPI Setup
- M2 Resume Upload
- M3 Resume Parser
- M3.5 Resume Processing Pipeline
- M4 Database Infrastructure
- M5 Database Models
- M6 Alembic Migration
- M7 Repository Layer
- M8 Resume Persistence

---

# Phase 2 — Resume Management

- M9 Resume Versioning
- M10 Resume Library
- M11 Resume Performance Analytics

---

# Phase 3 — Intelligent Job Discovery

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

---

# Phase 4 — AI Intelligence

- M22 Job Evaluation Engine
- M23 Skills Gap Analysis
- M24 Recommendation Engine
- M25 Resume Tailoring
- M26 Cover Letter Generator
- M27 Application Answer Generator

---

# Phase 5 — Automation

- M28 Automation Capability Detection
- M29 Application Rules Engine
- M30 Approval Queue
- M31 Playwright Automation Engine
- M32 Intervention Queue
- M33 Application Tracker

---

# Phase 6 — Dashboard & Insights

- M34 Dashboard
- M35 Analytics
- M36 Company Intelligence
- M37 Personal Job Search Memory
- M38 Interview Knowledge Base
- M39 Notifications & Scheduler
- M40 Production Hardening