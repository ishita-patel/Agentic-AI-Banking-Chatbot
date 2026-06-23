# backend/agents/base_agent.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
from groq import Groq

class BaseAgent(ABC):
    """Base class for all agents - all use LLM"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.capabilities = []
        
        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            self.client = Groq(api_key=api_key)
            self.llm_available = True
        else:
            self.client = None
            self.llm_available = False
    
    @abstractmethod
    async def process(self, user_id: str, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        pass
    
    async def get_llm_response(self, system_prompt: str, user_query: str) -> str:
        """Get response from LLM with domain-specific prompt"""
        if not self.llm_available:
            return "LLM service is not available. Please check your API key."
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error: {str(e)}"
    
    def get_capabilities(self) -> list:
        return self.capabilities
    
    def can_handle(self, task_type: str) -> bool:
        return task_type in self.capabilities