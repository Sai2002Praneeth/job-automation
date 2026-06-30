from fastapi import FastAPI
from api.resume import router as resume_router

app = FastAPI(
    title="AI Job Automation Platform",
    description="Backend API for the AI Job Automation platform.",
    version="1.0.0",
)

app.include_router(resume_router)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}