"""
Local File Store.
Provides persistent local storage for session data using JSON files.
Used as a fallback when Redis is unavailable.
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class LocalFileStore:
    """
    File-based session storage that survives application restarts.
    
    Sessions are stored as individual JSON files in a data directory.
    This provides a local fallback when Redis is unavailable.
    """
    
    def __init__(self, data_dir: str = "data/sessions"):
        """
        Initialize the local file store.
        
        Args:
            data_dir: Directory path for storing session files.
        """
        self.data_dir = Path(data_dir)
        self._ensure_data_dir()
    
    def _ensure_data_dir(self) -> None:
        """Create data directory if it doesn't exist."""
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create data directory: {e}")
    
    def _session_path(self, session_id: str) -> Path:
        """Get file path for a session ID."""
        # Sanitize session ID to prevent directory traversal
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.data_dir / f"{safe_id}.json"
    
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve session data from file storage.
        
        Args:
            session_id: The unique session identifier.
        
        Returns:
            Session data dict or None if not found.
        """
        path = self._session_path(session_id)
        
        if not path.exists():
            return None
        
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # Check TTL expiration
            if "expires_at" in data:
                expires_at = datetime.fromisoformat(data["expires_at"])
                if datetime.now() > expires_at:
                    logger.info(f"Session {session_id} has expired, removing")
                    self.delete(session_id)
                    return None
            
            return data.get("session_data")
            
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to read session {session_id}: {e}")
            return None
    
    def set(self, session_id: str, data: Dict[str, Any], ttl_seconds: int = 86400) -> bool:
        """
        Store session data to file.
        
        Args:
            session_id: The unique session identifier.
            data: Session data to store.
            ttl_seconds: Time to live in seconds (default: 24 hours).
        
        Returns:
            True if successful, False otherwise.
        """
        path = self._session_path(session_id)
        
        try:
            expires_at = datetime.now().isoformat()
            if ttl_seconds > 0:
                from datetime import timedelta
                expires_at = (datetime.now() + timedelta(seconds=ttl_seconds)).isoformat()
            
            file_data = {
                "session_id": session_id,
                "session_data": data,
                "created_at": datetime.now().isoformat(),
                "expires_at": expires_at,
            }
            
            with open(path, "w", encoding="utf-8") as f:
                json.dump(file_data, f, indent=2)
            
            return True
            
        except IOError as e:
            logger.error(f"Failed to write session {session_id}: {e}")
            return False
    
    def delete(self, session_id: str) -> bool:
        """
        Delete a session file.
        
        Args:
            session_id: The unique session identifier.
        
        Returns:
            True if deleted, False otherwise.
        """
        path = self._session_path(session_id)
        
        try:
            if path.exists():
                path.unlink()
            return True
        except IOError as e:
            logger.warning(f"Failed to delete session {session_id}: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired session files.
        
        Returns:
            Number of sessions cleaned up.
        """
        cleaned = 0
        
        try:
            for path in self.data_dir.glob("*.json"):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    if "expires_at" in data:
                        expires_at = datetime.fromisoformat(data["expires_at"])
                        if datetime.now() > expires_at:
                            path.unlink()
                            cleaned += 1
                            
                except (json.JSONDecodeError, IOError):
                    continue
                    
        except Exception as e:
            logger.warning(f"Error during cleanup: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} expired sessions")
        
        return cleaned
