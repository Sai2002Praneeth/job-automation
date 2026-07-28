from fastapi import FastAPI
from api.health import router as health_router
from api.job import router as job_router
from api.resume import router as resume_router


app = FastAPI(
    title="AI Job Automation Platform",
    description="Backend API for the AI Job Automation platform.",
    version="1.0.0",
)

app.include_router(health_router)
app.include_router(job_router)
app.include_router(resume_router)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
