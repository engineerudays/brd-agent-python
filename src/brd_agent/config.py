"""
BRD Agent - Configuration
Loads settings from environment variables with sensible defaults
"""

import os
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # === Anthropic API ===
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude"
    )
    
    # === Model Configuration ===
    llm_model: str = Field(
        default="claude-3-haiku-20240307",
        description="LLM model to use"
    )
    llm_max_tokens: int = Field(
        default=4096,
        description="Maximum tokens for LLM response"
    )
    llm_temperature: float = Field(
        default=0.7,
        description="Temperature for LLM generation (0.0-1.0)"
    )
    
    # === API Configuration ===
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host"
    )
    api_port: int = Field(
        default=8000,
        description="API server port"
    )
    
    # === Logging ===
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # === Paths ===
    @property
    def project_root(self) -> Path:
        """Get the project root directory"""
        return Path(__file__).parent.parent.parent.parent
    
    @property
    def prompts_dir(self) -> Path:
        """Get the prompts directory"""
        return Path(__file__).parent / "prompts"
    
    @property
    def sample_inputs_dir(self) -> Path:
        """Get the sample inputs directory"""
        return self.project_root / "sample_inputs"
    
    @property
    def outputs_dir(self) -> Path:
        """Get the outputs directory"""
        return self.sample_inputs_dir / "outputs"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False  # Allow ANTHROPIC_API_KEY or anthropic_api_key


# Global settings instance
# This will be loaded once when the module is imported
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get the application settings.
    Creates the settings instance on first call (lazy loading).
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """
    Reload settings from environment.
    Useful for testing or when env vars change.
    """
    global _settings
    _settings = Settings()
    return _settings

