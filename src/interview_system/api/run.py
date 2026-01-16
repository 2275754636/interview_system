#!/usr/bin/env python3
"""
FastAPI server launcher
Usage: python -m interview_system.api.run
"""

import uvicorn
from interview_system.api.main import app


def main():
    """Start FastAPI server"""
    uvicorn.run(
        "interview_system.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
