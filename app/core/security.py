"""
API Key authentication middleware.
Validates X-API-KEY header on protected endpoints.
"""
from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import get_settings

# Define the header scheme
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the API key from the X-API-KEY header.
    
    Raises:
        HTTPException: If API key is missing or invalid.
    
    Returns:
        The validated API key.
    """
    settings = get_settings()
    
    if not api_key:
        import logging
        logging.getLogger(__name__).warning("Missing X-API-KEY header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Include X-API-KEY header.",
        )
    
    if api_key != settings.API_SECRET_KEY:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Invalid API key provided: {api_key[:3]}...{api_key[-3:] if len(api_key) > 6 else ''}")
        logger.info(f"Expected key starts with: {settings.API_SECRET_KEY[:3] if settings.API_SECRET_KEY else 'None'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    
    return api_key
