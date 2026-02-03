"""
Pydantic models for webhook request and response.
Matches the API contract from 01_Problem_Statement.md
"""
from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, ConfigDict


class MessageInput(BaseModel):
    """Individual message in a conversation."""
    model_config = ConfigDict(extra="ignore")

    sender: Literal["scammer", "user"] = Field(
        ..., description="Who sent the message (e.g., 'scammer', 'user')"
    )
    text: str = Field(..., description="The message content")
    timestamp: datetime = Field(
        default_factory=datetime.now, 
        description="When the message was sent"
    )


class MetadataInput(BaseModel):
    """Request metadata for context."""
    model_config = ConfigDict(extra="ignore")

    channel: Literal["SMS", "WhatsApp", "Email", "Chat"] = Field(
        default="SMS", description="Communication channel (SMS, WhatsApp, etc.)"
    )
    language: str = Field(default="en", description="Language code")
    locale: str = Field(default="IN", description="Locale/region code")


class WebhookRequest(BaseModel):
    """
    Incoming webhook payload from the external system.
    This is the input to our honey-pot API.
    """
    model_config = ConfigDict(extra="ignore")

    sessionId: str = Field(..., description="Unique session identifier")
    message: MessageInput = Field(..., description="The current incoming message")
    conversationHistory: List[MessageInput] = Field(
        default_factory=list,
        description="Previous messages in this conversation"
    )
    metadata: Optional[MetadataInput] = Field(
        default_factory=MetadataInput,
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
