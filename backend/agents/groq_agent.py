# backend/agents/groq_agent.py

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


class GroqAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")

        self.is_available = False
        self.client = None

        if self.api_key and self.api_key.startswith("gsk_"):
            try:
                self.client = Groq(api_key=self.api_key)
                self.is_available = True
                print("✅ Groq AI initialized")
            except Exception as e:
                print(f"❌ Groq initialization error: {e}")

    async def process(
        self,
        message: str,
        user_id: str = "default",
        system_prompt: str = None,
        temperature: float = 0.3,
        max_tokens: int = 1000
    ) -> str:
        """
        Generic LLM processor.

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

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt or default_prompt
                    },
                    {
                        "role": "user",
                        "content": message
                    }
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Groq Error: {e}")
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
            system_prompt=routing_prompt,
            temperature=0
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
            system_prompt="You are an expert response synthesizer."
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
            system_prompt="You are a banking query classifier.",
            temperature=0
        )