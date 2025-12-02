"""
BRD Agent - LLM Service
Abstraction layer for LLM providers (Anthropic, Ollama, etc.)
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Optional

from anthropic import Anthropic

from ..config import get_settings

logger = logging.getLogger(__name__)


class LLMService(ABC):
    """
    Abstract base class for LLM services.
    Implement this interface to add new LLM providers.
    """
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response (uses default if not specified)
            temperature: Temperature for generation (uses default if not specified)
            
        Returns:
            The generated text response
        """
        pass
    
    @abstractmethod
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """
        Generate a JSON response from the LLM.
        
        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt for context
            max_tokens: Maximum tokens in response
            temperature: Temperature for generation
            
        Returns:
            Parsed JSON as a dictionary
        """
        pass


class AnthropicLLM(LLMService):
    """
    Anthropic Claude LLM implementation.
    Uses the Anthropic Python SDK.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the Anthropic LLM client.
        
        Args:
            api_key: Anthropic API key (uses env var if not provided)
            model: Model name (uses config default if not provided)
            max_tokens: Default max tokens (uses config default if not provided)
            temperature: Default temperature (uses config default if not provided)
        """
        settings = get_settings()
        
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.llm_model
        self.default_max_tokens = max_tokens or settings.llm_max_tokens
        self.default_temperature = temperature or settings.llm_temperature
        
        if not self.api_key:
            raise ValueError(
                "Anthropic API key is required. "
                "Set ANTHROPIC_API_KEY environment variable or pass api_key parameter."
            )
        
        self.client = Anthropic(api_key=self.api_key)
        
        logger.info(f"Initialized AnthropicLLM with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Generate a response using Claude.
        
        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt
            max_tokens: Max tokens (uses default if not specified)
            temperature: Temperature (uses default if not specified)
            
        Returns:
            Generated text response
        """
        max_tokens = max_tokens or self.default_max_tokens
        temperature = temperature or self.default_temperature
        
        logger.debug(f"Generating response with model={self.model}, max_tokens={max_tokens}")
        
        # Build the message
        messages = [{"role": "user", "content": prompt}]
        
        # Make the API call
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": messages,
        }
        
        # Add system prompt if provided
        if system_prompt:
            kwargs["system"] = system_prompt
        
        # Add temperature if not default
        if temperature != 1.0:
            kwargs["temperature"] = temperature
        
        response = self.client.messages.create(**kwargs)
        
        # Extract text from response
        result = response.content[0].text
        
        logger.debug(f"Generated response: {len(result)} characters")
        
        return result
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """
        Generate a JSON response using Claude.
        Adds JSON formatting instructions to the prompt.
        
        Args:
            prompt: The user prompt/message
            system_prompt: Optional system prompt
            max_tokens: Max tokens
            temperature: Temperature
            
        Returns:
            Parsed JSON dictionary
        """
        # Enhance system prompt to request JSON output
        json_system = system_prompt or ""
        if json_system:
            json_system += "\n\n"
        json_system += (
            "You must respond with valid JSON only. "
            "Do not include any text before or after the JSON. "
            "Do not wrap the JSON in markdown code blocks."
        )
        
        # Generate the response
        response_text = self.generate(
            prompt=prompt,
            system_prompt=json_system,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Clean up the response (remove markdown code blocks if present)
        cleaned = response_text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        elif cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        cleaned = cleaned.strip()
        
        # Parse JSON
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response_text[:500]}...")
            raise ValueError(f"LLM returned invalid JSON: {e}")


class OllamaLLM(LLMService):
    """
    Ollama local LLM implementation.
    Placeholder for future implementation.
    """
    
    def __init__(
        self,
        model: str = "gemma2:9b",
        base_url: str = "http://localhost:11434",
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize the Ollama LLM client.
        
        Args:
            model: Model name (e.g., 'gemma2:9b', 'llama3:8b')
            base_url: Ollama server URL
            max_tokens: Default max tokens
            temperature: Default temperature
        """
        self.model = model
        self.base_url = base_url
        self.default_max_tokens = max_tokens or 4096
        self.default_temperature = temperature or 0.7
        
        logger.info(f"Initialized OllamaLLM with model: {self.model}")
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """Generate using Ollama - to be implemented when switching to local."""
        raise NotImplementedError(
            "OllamaLLM is not yet implemented. "
            "Use AnthropicLLM for now, or implement this method."
        )
    
    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> dict:
        """Generate JSON using Ollama - to be implemented when switching to local."""
        raise NotImplementedError(
            "OllamaLLM is not yet implemented. "
            "Use AnthropicLLM for now, or implement this method."
        )


def get_llm_service(provider: str = "anthropic", **kwargs) -> LLMService:
    """
    Factory function to get an LLM service instance.
    
    Args:
        provider: LLM provider name ('anthropic', 'ollama')
        **kwargs: Additional arguments passed to the LLM constructor
        
    Returns:
        LLMService instance
    """
    providers = {
        "anthropic": AnthropicLLM,
        "ollama": OllamaLLM,
    }
    
    if provider not in providers:
        raise ValueError(f"Unknown LLM provider: {provider}. Available: {list(providers.keys())}")
    
    return providers[provider](**kwargs)

