import os
from groq import Groq
from dotenv import load_dotenv
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
import time

load_dotenv()


class GroqAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        print("\n========== GROQ DEBUG ==========")
        print("KEY:", self.api_key[:15] + "...")
        print("================================\n")
        self.is_available = False
        self.client = None
        self.tracer = trace.get_tracer(__name__)
        self.MODEL_NAME = "llama-3.3-70b-versatile"

        if self.api_key and self.api_key.startswith("gsk_"):
            try:
                self.client = Groq(api_key=self.api_key)
                self.is_available = True
                print("Groq AI initialized")
            except Exception as e:
                print(f"Groq initialization error: {e}")

    async def process(
        self,
        message: str,
        user_id: str = "default",
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1000,
        operation: str = "general_chat"
    ) -> str:
        """
        Generic LLM processor.

        Args:
            message: User message
            user_id: User identifier for tracing
            system_prompt: System instructions
            temperature: LLM temperature
            max_tokens: Max tokens to generate
            operation: Operation name for trace (e.g., "query_analyzer", "synthesizer")

        Returns:
            Plain text string response.
        """

        if not self.is_available:
            return "AI service unavailable."

        default_prompt = """
            You are Aiko Bank's intelligent AI assistant.

            Responsibilities:
            - Help users with banking services
            - Analyze intent
            - Route requests
            - Summarize agent outputs
            - Answer financial questions

            Guidelines:
            - Be professional
            - Be concise
            - Be accurate
            - Be conversational
            - If information is unavailable, clearly say so
            """

        system_prompt = system_prompt or default_prompt
        
        with self.tracer.start_as_current_span("LLM Call") as span:
            span.set_attribute("operation", operation)
            span.set_attribute("model", self.MODEL_NAME)
            span.set_attribute("temperature", temperature)
            span.set_attribute("prompt_chars", len(message))
            
            try:
                start = time.time()
                
                response = self.client.chat.completions.create(
                    model=self.MODEL_NAME,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                output = response.choices[0].message.content.strip()
                
                # Calculate metrics
                latency = time.time() - start
                response_chars = len(output)
                
                # Update OpenTelemetry span
                span.set_attribute("latency_seconds", latency)
                span.set_attribute("response_chars", response_chars)
                span.set_attribute("success", True)
                
                # Handle usage safely - Groq usually returns it but guard anyway
                if hasattr(response, "usage") and response.usage:
                    span.set_attribute("prompt_tokens", response.usage.prompt_tokens)
                    span.set_attribute("completion_tokens", response.usage.completion_tokens)
                    span.set_attribute("total_tokens", response.usage.total_tokens)
                
                return output

            except Exception as e:
                print(f"Groq Error: {e}")
                
                # Record exception in OpenTelemetry
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR))
                span.set_attribute("success", False)
                
                return "I encountered an error while processing your request."

    async def route_query(self, query: str) -> str:
        """
        Specialized routing helper.
        """

        routing_prompt = """
        You are an AI routing engine.

        Available domains:

        balance
        statement
        loan
        travel
        calculator
        health
        investment
        tax
        legal
        web_search
        rag
        general

        Return ONLY ONE domain name.
        No explanation.
        """

        return await self.process(
            query,
            user_id="router",
            system_prompt=routing_prompt,
            temperature=0,
            operation="route_query"
        )

    async def summarize(
        self,
        user_query: str,
        agent_outputs: list
    ) -> str:
        """
        Combine multiple agent outputs into one answer.
        """

        content = "\n\n".join(agent_outputs)

        prompt = f"""
        You are a response synthesizer.

        User Query:
        {user_query}

        Agent Responses:
        {content}

        Create ONE natural conversational response.

        Rules:
        - Do not mention agents.
        - Do not mention internal systems.
        - Merge all information naturally.
        - Keep under 300 words.
        """

        return await self.process(
            prompt,
            user_id="synthesizer",
            system_prompt="You are an expert response synthesizer.",
            operation="synthesizer"
        )

    async def analyze_intent(self, query: str) -> str:
        """
        Returns JSON string.
        Used by QueryAnalyzer.
        """

        prompt = f"""
        Analyze this user query.

        Query:
        {query}

        Return ONLY valid JSON.

        {{
            "primary_domain":"",
            "secondary_domains":[],
            "intent":"",
            "complexity":"simple",
            "confidence":0.0
        }}
"""

        return await self.process(
            prompt,
            user_id="query_analyzer",
            system_prompt="You are a banking query classifier.",
            temperature=0,
            operation="analyze_intent"
        )