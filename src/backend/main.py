from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.backend.dashboard import (
    router as dashboard_router
)

from src.backend.pipeline import (
    router as pipeline_router
)


# ============================================================
# CREATE FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="Cloud Data Engineering Pipeline API",
    description=(
        "Backend API for the end-to-end "
        "cloud data engineering pipeline"
    ),
    version="1.0.0"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],

    allow_credentials=True,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ],
)


# ============================================================
# REGISTER ROUTERS
# ============================================================

# Dashboard APIs
app.include_router(
    dashboard_router
)


# Pipeline APIs
app.include_router(
    pipeline_router
)


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "success": True,
        "message": (
            "Cloud Data Engineering Pipeline "
            "API is running."
        ),
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "success": True,
        "status": "healthy",
    }