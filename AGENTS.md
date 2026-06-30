# AGENTS.md

## Project

AI Job Automation Platform

Tech Stack

* Python 3.13
* FastAPI
* Playwright
* PostgreSQL
* TypeScript
* VS Code

---

## Architecture

Always follow layered architecture.

API Router
↓

Service Layer
↓

Database / File System

Business logic must never be placed inside API routers.

Keep `main.py` minimal.

---

## Project Structure

backend/
api/
services/
models/
database/

automation/
playwright/
sites/
pages/

frontend/

resume/

generated/

---

## Coding Standards

* Use Python type hints.
* Use async FastAPI endpoints where appropriate.
* Keep functions small.
* Write readable code.
* Avoid duplicate code.
* Prefer composition over large classes.

---

## File Rules

Modify only the files requested.

Do not refactor unrelated code.

Do not rename files unless instructed.

Do not create unnecessary files.

---

## Dependencies

Do not install new packages unless necessary.

Reuse existing libraries whenever possible.

---

## Error Handling

Use proper HTTPException for API errors.

Return meaningful JSON responses.

Never hide exceptions silently.

---

## Security

Validate all user inputs.

Never trust uploaded files.

Do not expose secrets.

---

## Workflow

After implementing a feature:

1. Verify the code.
2. Ensure imports are correct.
3. Ensure no syntax errors.
4. Report modified files.

Do not perform Git operations.

Do not modify AGENTS.md unless requested.