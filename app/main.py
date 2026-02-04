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

# Add diagnostic middleware to log all traffic
@app.middleware("http")
async def diagnostic_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    # Log request basics
    method = request.method
    path = request.url.path
    query = str(request.query_params)
    
    # Try to peek into body if it's small
    body_peek = "not-json"
    if "application/json" in request.headers.get("content-type", ""):
        try:
            body_bytes = await request.body()
            # We must replace the stream so the route can read it again
            async def receive():
                return {"type": "http.request", "body": body_bytes}
            request._receive = receive
            body_peek = body_bytes.decode()[:500] 
        except:
            body_peek = "peek-failed"

    response: Response = await call_next(request)
    
    # Try to peek into response body
    response_body = "not-peeked"
    if response.status_code == 200 and "application/json" in response.headers.get("content-type", ""):
        try:
            # We have to iterate the iterator
            body = b""
            async for chunk in response.body_iterator:
                body += chunk
            # Re-create the iterator so the response continues to the client
            response.body_iterator = _create_iterator(body)
            response_body = body.decode()[:500]
        except Exception as e:
            response_body = f"peek-failed: {str(e)}"

    duration = time.time() - start_time
    
    logger.info(
        f"DIAGNOSTIC: {method} {path} | Status: {response.status_code} | "
        f"Duration: {duration:.3f}s | Req: {body_peek} | Res: {response_body}"
    )
    return response

async def _create_iterator(body: bytes):
    yield body

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
    error_msg = str(exc.errors())
    logger.error(f"RAW_VALIDATION_ERROR on {request.url.path}: {error_msg}")
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
