"""
Development server entry point.
Run with: python run.py
"""
import os
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=True,  # Enable hot reload for development
        log_level="info",
    )
