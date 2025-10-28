"""
Hurricane Risk API - FastAPI application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import risk

app = FastAPI(
    title="Hurricane Risk API",
    description="API for calculating traveler risk exposure from hurricane impacts",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(risk.router, prefix="/api/v1", tags=["risk"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "Hurricane Risk API",
        "version": "1.0.0",
        "docs": "/docs"
    }

