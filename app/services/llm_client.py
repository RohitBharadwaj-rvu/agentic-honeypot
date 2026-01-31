"""
OpenRouter LLM Client.
Provides async interface to OpenRouter API with model fallback support.
"""
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class ModelType(Enum):
    """Model selection for different tasks."""
    ROLEPLAY = "roleplay"      # For persona engagement
    REASONING = "reasoning"    # For detection/extraction
    FALLBACK = "fallback"      # General fallback


@dataclass
class ChatMessage:
    """Chat message structure."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LLMResponse:
    """Response from LLM."""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: str


class LLMClient:
    """
    Async client for OpenRouter API.
    Supports model fallback and temperature configuration.
    """
    
    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENROUTER_API_KEY
        self.base_url = settings.OPENROUTER_BASE_URL
        
        # Model mapping
        self._models = {
            ModelType.ROLEPLAY: settings.MODEL_ROLEPLAY,
            ModelType.REASONING: settings.MODEL_REASONING,
            ModelType.FALLBACK: settings.MODEL_FALLBACK,
        }
        
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "HTTP-Referer": "https://honeypot.local",  # Required by OpenRouter
                    "X-Title": "Agentic Honeypot",
                },
                timeout=60.0,  # LLMs can be slow
            )
        return self._client
    
    def _get_model(self, model_type: ModelType) -> str:
        """Get model name for type."""
        return self._models.get(model_type, self._models[ModelType.FALLBACK])
    
    async def chat(
        self,
        messages: List[ChatMessage],
        model_type: ModelType = ModelType.ROLEPLAY,
        temperature: float = 0.7,
        max_tokens: int = 500,
        use_fallback: bool = True,
    ) -> LLMResponse:
        """
        Send chat completion request to OpenRouter.
        
        Args:
            messages: List of chat messages
            model_type: Which model to use
            temperature: Sampling temperature (0 = deterministic)
            max_tokens: Maximum response tokens
            use_fallback: Whether to try fallback model on failure
        
        Returns:
            LLMResponse with content and metadata
        """
        client = await self._get_client()
        model = self._get_model(model_type)
        
        payload = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            logger.info(f"Calling OpenRouter model: {model}")
            response = await client.post("/chat/completions", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                choice = data["choices"][0]
                return LLMResponse(
                    content=choice["message"]["content"],
                    model=data.get("model", model),
                    usage=data.get("usage", {}),
                    finish_reason=choice.get("finish_reason", "stop"),
                )
            else:
                error_text = response.text
                logger.warning(f"Model {model} failed with {response.status_code}: {error_text}")
                
                # Try fallback if enabled
                if use_fallback and model_type != ModelType.FALLBACK:
                    logger.info("Trying fallback model...")
                    return await self.chat(
                        messages=messages,
                        model_type=ModelType.FALLBACK,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        use_fallback=False,
                    )
                
                raise Exception(f"LLM request failed: {error_text}")
                
        except httpx.TimeoutException:
            logger.error(f"Timeout calling model {model}")
            if use_fallback and model_type != ModelType.FALLBACK:
                return await self.chat(
                    messages=messages,
                    model_type=ModelType.FALLBACK,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    use_fallback=False,
                )
            raise
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """Get the singleton LLM client instance."""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
