import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

class GroqAgent:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key and self.api_key.startswith("gsk_"):
            try:
                self.client = Groq(api_key=self.api_key)
                self.is_available = True
                print("Groq AI is ready")
            except Exception as e:
                print(f"Groq initialization error: {e}")
                self.is_available = False
        else:
            print("No valid GROQ_API_KEY found")
            self.is_available = False
    
    async def process(self, message, user_id):
        if not self.is_available:
            return {
                "response": "AI assistant is not configured. Please contact support.",
                "agent": "GroqAgent",
                "ai_used": False
            }
        
        system_prompt = (
            "You are a banking assistant for Agentic Bank. Follow these rules strictly:\n\n"
            "1. If the user asks about banking services (balance, statements, loans, cards, transfers, fixed deposits), answer helpfully.\n"
            "2. If the user asks about anything NOT related to banking (jokes, general knowledge, sports, weather, politics, entertainment, etc.), "
            "politely respond: 'I apologize, but I am a banking assistant and can only help with banking-related queries. "
            "I can assist you with balance inquiries, statements, loans, fund transfers, card services, and fixed deposits. "
            "How may I help you with your banking today?'\n"
            "3. Keep responses concise and professional.\n"
            "4. Do not answer non-banking questions under any circumstances.\n\n"
            "Example:\n"
            'User: "Tell me a joke"\n'
            'Response: "I apologize, but I am a banking assistant and can only help with banking-related queries. '
            'I can assist you with balance inquiries, statements, and loans. How may I help you today?"'
        )

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=200
            )
            
            bot_response = response.choices[0].message.content
            
            return {
                "response": bot_response,
                "agent": "GroqAgent",
                "ai_used": True
            }
            
        except Exception as e:
            print(f"Groq error: {e}")
            return {
                "response": "I am a banking assistant. I can help you with balance inquiries, statements, loans, and other banking services. How can I assist you today?",
                "agent": "GroqAgent",
                "ai_used": False
            }