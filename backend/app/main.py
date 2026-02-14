from fastapi import FastAPI

app = FastAPI(
    title="AERAE Accelerator API",
    description="Backend API for the AERAE Accelerator platform",
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "ok"}
