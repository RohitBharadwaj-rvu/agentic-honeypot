"""
Agentic Honey-Pot API
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.core.routes import router
from app.services import get_session_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting Honey-Pot API...")
    settings = get_settings()
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize session manager (lazy, but log status)
    session_manager = get_session_manager()
    logger.info("Session manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Honey-Pot API...")
    await session_manager.close()
    logger.info("Session manager closed")


# Create FastAPI app
app = FastAPI(
    title="Agentic Honey-Pot API",
    description="AI-powered scam detection and engagement system",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    """Return informative error for debugging validation issues."""
    logger.error(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Invalid request body.",
            "errors": exc.errors(),
            "body": getattr(exc, "body", None)
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Agentic Honey-Pot API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }
