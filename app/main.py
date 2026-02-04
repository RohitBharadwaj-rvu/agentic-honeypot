"""
Agentic Honey-Pot API
Main FastAPI application entry point.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi import status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import time
import json

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

@app.middleware("http")
async def diagnostic_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request basics
    method = request.method
    path = request.url.path
    
    try:
        response: Response = await call_next(request)
    except Exception as e:
        logger.error(f"Middleware caught unhandled exception: {e}", exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "Internal Server Error"})

    duration = time.time() - start_time
    
    logger.info(
        f"DIAGNOSTIC: {method} {path} | Status: {response.status_code} | "
        f"Duration: {duration:.3f}s"
    )
    return response

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Verbose validation error for GUVI debugging."""
    try:
        body = await request.body()
        body_str = body.decode()
    except:
        body_str = "could not read body"
        
    error_msg = str(exc.errors())
    logger.error(f"VALIDATION_ERROR | {request.method} {request.url.path} | Body: {body_str} | Error: {error_msg}")
    
    return JSONResponse(
        status_code=400,
        content={
            "status": "error",
            "detail": "INVALID_REQUEST_BODY",
            "debug_info": exc.errors()
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Agentic Honey-Pot API",
        "version": "0.2.4-final-valuation",
        "status": "active",
        "endpoints": ["/webhook", "/api/honeypot", "/health"],
    }
