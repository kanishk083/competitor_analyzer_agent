"""
Competitor Analyzer Agent - Main Entry Point
Run the FastAPI webhook listener server.
"""

import uvicorn
from app import app
from config.settings import settings


def main():
    """Run the FastAPI server."""
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
