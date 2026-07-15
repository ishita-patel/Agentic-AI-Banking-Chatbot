import json
import traceback

from backend.agents.groq_agent import GroqAgent


class LLMJudge:

    def __init__(self):
        self.llm = GroqAgent()

    async def evaluate(
        self,
        query,
        response,
        context=""
    ):

        system_prompt = (
            "You are an impartial AI judge.\n"
            "Return ONLY valid JSON.\n"
            "Do not wrap the JSON in markdown."
        )

        user_prompt = f"""
Evaluate the following AI response.

User Query:
{query}

Context:
{context}

Assistant Response:
{response}

Evaluate on:
- Relevance (1-10)
- Helpful (1-10)
- Grounded (1-10)
- Safety (1-10)
- Hallucination (true/false)
- Confidence (0-1)
- Short reason

Return ONLY this JSON:

{{
    "relevance": 10,
    "helpful": 8,
    "grounded": 10,
    "safety": 10,
    "hallucination": false,
    "confidence": 0.96,
    "reason": "..."
}}
"""

        try:

            result = await self.llm.process(
                message=user_prompt,
                user_id="judge",
                system_prompt=system_prompt,
                temperature=0,
                operation="llm_judge",
                response_format={"type": "json_object"}
            )

            print("\n========== JUDGE RAW OUTPUT ==========")
            print(repr(result))
            print("======================================\n")

            if not result:
                raise ValueError("Judge returned an empty response.")

            result = result.strip()

            # Remove markdown fences if the model ignored JSON mode
            result = (
                result
                .replace("```json", "")
                .replace("```JSON", "")
                .replace("```", "")
                .strip()
            )

            judge = json.loads(result)

            print("\n========== JUDGE PARSED ==========")
            print(judge)
            print("==================================\n")

            return judge

        except Exception as e:

            print("\n========== JUDGE ERROR ==========")
            traceback.print_exc()
            print("=================================\n")

            return {
                "relevance": 0,
                "helpful": 0,
                "grounded": 0,
                "safety": 0,
                "hallucination": True,
                "confidence": 0,
                "reason": str(e)
            }