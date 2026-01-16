"""FastAPI application entry point"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import session

app = FastAPI(
    title="Interview System API",
    version="2.0.0",
    description="REST API for AI-powered interview platform",
)

# CORS configuration for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev port
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(session.router, prefix="/api")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "interview-system"}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "Interview System API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }
