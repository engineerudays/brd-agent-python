"""
BRD Agent - Base Agent
Abstract base class for all agents in the system
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional

from ..services.llm import LLMService, get_llm_service


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all BRD agents.
    
    Each agent:
    - Has a name and description
    - Uses an LLM service for generation
    - Implements a run() method to execute its task
    """
    
    name: str = "BaseAgent"
    description: str = "Base agent class"
    
    def __init__(
        self,
        llm_service: Optional[LLMService] = None,
        **kwargs
    ):
        """
        Initialize the agent.
        
        Args:
            llm_service: LLM service to use (creates default if not provided)
            **kwargs: Additional arguments passed to LLM service creation
        """
        self.llm = llm_service or get_llm_service(**kwargs)
        logger.info(f"Initialized {self.name}")
    
    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        Execute the agent's main task.
        
        Args:
            input_data: Input data for the agent to process
            
        Returns:
            The agent's output
        """
        pass
    
    def _load_prompt(self, prompt_name: str) -> str:
        """
        Load a prompt template from the prompts directory.
        
        Args:
            prompt_name: Name of the prompt file (without .txt extension)
            
        Returns:
            Prompt template string
        """
        from ..config import get_settings
        
        settings = get_settings()
        prompt_path = settings.prompts_dir / f"{prompt_name}.txt"
        
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt not found: {prompt_path}")
        
        return prompt_path.read_text()
    
    def _format_prompt(self, template: str, **kwargs) -> str:
        """
        Format a prompt template with variables.
        
        Args:
            template: Prompt template with {variable} placeholders
            **kwargs: Variables to substitute
            
        Returns:
            Formatted prompt string
        """
        return template.format(**kwargs)
    
    def __repr__(self) -> str:
        return f"<{self.name}>"

