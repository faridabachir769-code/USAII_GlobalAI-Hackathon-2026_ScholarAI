#!/usr/bin/env python
"""
Run the FastAPI application locally.

Usage:
    python run.py              # Run on default port 8000
    python run.py --port 8001  # Run on custom port

The server will be available at http://localhost:8000
Interactive API docs at http://localhost:8000/docs
"""

import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # Module:app
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,  # Auto-reload on file changes
        log_level="info",
    )
