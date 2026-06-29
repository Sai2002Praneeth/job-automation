from fastapi import FastAPI

# Initialize the FastAPI application with project metadata.
app = FastAPI(
    title="AI Job Automation Platform",
    description="Backend API for the AI Job Automation platform.",
    version="1.0.0",
)


# Root endpoint providing a welcome message.
@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Welcome to the AI Job Automation Platform"}


# Health-check endpoint for monitoring API availability.
@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}