"""
Pydantic models for webhook request and response.
Matches the API contract from 01_Problem_Statement.md
"""
from datetime import datetime
from typing import List, Literal, Optional, Any, Union
from pydantic import BaseModel, Field, ConfigDict, AliasChoices


class MessageInput(BaseModel):
    """Individual message in a conversation."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    sender: str = Field(
        default="scammer", 
        validation_alias=AliasChoices("sender"),
        description="Who sent the message"
    )
    text: str = Field(
        default="", 
        validation_alias=AliasChoices("text"),
        description="The message content"
    )
    timestamp: Optional[Any] = Field(
        default=None, 
        validation_alias=AliasChoices("timestamp", "time"),
        description="When the message was sent"
    )


class MetadataInput(BaseModel):
    """Request metadata for context."""
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    channel: str = Field(
        default="SMS", 
        validation_alias=AliasChoices("channel"),
        description="Communication channel"
    )
    language: str = Field(
        default="English", 
        validation_alias=AliasChoices("language", "lang"),
        description="Language"
    )
    locale: str = Field(
        default="IN", 
        validation_alias=AliasChoices("locale"),
        description="Locale"
    )


class WebhookRequest(BaseModel):
    """
    Incoming webhook payload from the external system.
    Extremely flexible to handle spec deviations.
    """
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    sessionId: Any = Field(
        default="session-missing",
        validation_alias=AliasChoices("sessionId", "session_id", "id", "sessionID"), 
        description="Unique session identifier"
    )
    message: Any = Field(
        default=None, 
        validation_alias=AliasChoices("message", "msg"),
        description="The current incoming message (nested or flat)"
    )
    # Extra fields for flat structure support
    text: Optional[str] = None
    sender: Optional[str] = None
    
    conversationHistory: List[Any] = Field(
        default_factory=list,
        validation_alias=AliasChoices("conversationHistory", "conversation_history", "history", "messages"),
        description="Previous messages in this conversation"
    )
    metadata: Any = Field(
        default_none=True,
        validation_alias=AliasChoices("metadata", "meta"),
        description="Channel and locale information"
    )


class WebhookResponse(BaseModel):
    """
    Synchronous response sent back to the caller.
    Contains the agent's reply to the scammer.
    """
    status: Literal["success", "error"] = Field(..., description="Response status")
    reply: str = Field(..., description="The agent's reply message")
    error: Optional[str] = Field(default=None, description="Error message if status is error")
