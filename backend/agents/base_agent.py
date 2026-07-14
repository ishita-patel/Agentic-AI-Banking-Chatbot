from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from backend.agents.groq_agent import GroqAgent

class BaseAgent(ABC):
    """Base class for all agents - all use LLM"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.capabilities = []
        
        # Initialize GroqAgent
        self.llm = GroqAgent()
        self.llm_available = self.llm.is_available
    
    @abstractmethod
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        pass
    
    async def get_llm_response(self, system_prompt: str, user_query: str, context: Dict[str, Any] = None) -> str:
        """Get response from LLM with domain-specific prompt"""
        if not self.llm_available:
            return "LLM service is not available. Please check your API key."
        
        try:
            return await self.llm.process(
                message=user_query,
                user_id=(
                    context.get("user_id")
                    if context
                    else "unknown"
                ),
                system_prompt=system_prompt,
                operation=self.name,
            )
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_capabilities(self) -> list:
        return self.capabilities
    
    def can_handle(self, task_type: str) -> bool:
        return task_type in self.capabilities