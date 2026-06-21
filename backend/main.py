from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from datetime import datetime, date
import uuid
import os
import sys
import io
from dotenv import load_dotenv
from pymongo import MongoClient

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from intent_classifier import IntentClassifier
from balance_agent import BalanceAgent
from groq_agent import GroqAgent
from loan_agent import LoanAgent
from statement_agent import StatementAgent
from servicing_agent import ServicingAgent
from encryption import encryption_manager
from data_loader import BankDataLoader

load_dotenv()

app = FastAPI(title="Agentic Bank Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

intent_classifier = IntentClassifier()
balance_agent = BalanceAgent()
groq_agent = GroqAgent()
loan_agent = LoanAgent()
statement_agent = StatementAgent()
servicing_agent = ServicingAgent()
data_loader = BankDataLoader()

MONGODB_URL = os.getenv("MONGODB_URL")
if MONGODB_URL:
    client = MongoClient(MONGODB_URL)
    db = client["bank_chatbot"]
    sessions_collection = db["sessions"]
    chat_history_collection = db["chat_history"]
    rate_limit_collection = db["rate_limit"]
    print("Connected to MongoDB")
else:
    print("MONGODB_URL not found, using in-memory storage")
    sessions_collection = None
    chat_history_collection = None
    rate_limit_collection = None

class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    session_id: str
    response: str
    intent: str
    ai_used: bool = False
    timestamp: datetime

sessions = {}

def check_rate_limit(user_id: str) -> bool:
    if rate_limit_collection is None:
        return True
    
    today = date.today().isoformat()
    record = rate_limit_collection.find_one({"user_id": user_id, "date": today})
    
    if not record:
        return True
    
    return record["count"] < 5

def increment_rate_limit(user_id: str):
    if rate_limit_collection is not None:
        today = date.today().isoformat()
        rate_limit_collection.update_one(
            {"user_id": user_id, "date": today},
            {"$inc": {"count": 1}},
            upsert=True
        )

@app.get("/")
def root():
    return {"message": "Bank Chatbot API", "status": "running"}

@app.get("/health")
def health_check():
    db_status = "connected" if MONGODB_URL else "in-memory"
    ai_status = "available" if groq_agent.is_available else "not configured"
    return {"status": "healthy", "database": db_status, "ai": ai_status, "timestamp": datetime.now()}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not check_rate_limit(request.user_id):
        raise HTTPException(
            status_code=429,
            detail="Daily limit reached (5 interactions). Please try again tomorrow."
        )
    
    user = data_loader.get_user(request.user_id)
    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid user. Please login again."
        )
    
    classification = intent_classifier.classify(request.message)
    agent_name = classification["agent"]
    intent_metadata = classification.get("metadata", {})
    ai_used = False
    bot_response = ""
    
    if agent_name == "balance":
        agent_result = await balance_agent.process(request.user_id, request.message)
        bot_response = agent_result["response"]
    
    elif agent_name == "statement":
        agent_result = await statement_agent.process(request.user_id, request.message)
        bot_response = agent_result["response"]
    
    elif agent_name == "loan":
        agent_result = await loan_agent.process(request.user_id, request.message)
        bot_response = agent_result["response"]
    
    elif agent_name == "servicing":
        service_type = intent_metadata.get("service_type", "complaint")
        agent_result = await servicing_agent.process(request.user_id, request.message, service_type)
        bot_response = agent_result["response"]
    
    else:
        ai_result = await groq_agent.process(request.message, request.user_id)
        bot_response = ai_result["response"]
        ai_used = ai_result.get("ai_used", False)
    
    session_id = str(uuid.uuid4())
    
    if sessions_collection is not None:
        encrypted_user_message = encryption_manager.encrypt(request.message)
        encrypted_bot_response = encryption_manager.encrypt(bot_response)
        
        sessions_collection.insert_one({
            "session_id": session_id,
            "user_id": request.user_id,
            "created_at": datetime.now(),
            "intent": agent_name,
            "ai_used": ai_used
        })
        
        chat_history_collection.insert_one({
            "session_id": session_id,
            "user_id": request.user_id,
            "user_message_encrypted": encrypted_user_message,
            "bot_response_encrypted": encrypted_bot_response,
            "intent": agent_name,
            "ai_used": ai_used,
            "confidence": classification["confidence"],
            "layer": classification["layer"],
            "created_at": datetime.now()
        })
    else:
        sessions[session_id] = {
            "user_id": request.user_id,
            "created_at": datetime.now(),
            "message": request.message
        }
    
    increment_rate_limit(request.user_id)
    
    return ChatResponse(
        session_id=session_id,
        response=bot_response,
        intent=agent_name,
        ai_used=ai_used,
        timestamp=datetime.now()
    )

@app.post("/statement")
async def generate_statement(request: ChatRequest):
    result = await statement_agent.process(request.user_id, request.message)
    
    if result.get("pdf_bytes"):
        pdf_bytes = result["pdf_bytes"]
        filename = result["filename"]
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    else:
        raise HTTPException(status_code=400, detail=result["response"])

@app.get("/rate-limit/{user_id}")
def get_rate_limit_status(user_id: str):
    if rate_limit_collection is not None:
        today = date.today().isoformat()
        record = rate_limit_collection.find_one({"user_id": user_id, "date": today})
        count = record["count"] if record else 0
        return {"user_id": user_id, "today_count": count, "limit": 5, "remaining": 5 - count}
    return {"message": "Rate limiting not configured"}

@app.get("/intent-test/{message}")
def test_intent(message: str):
    result = intent_classifier.classify(message)
    return result

@app.get("/ai-status")
def ai_status():
    return {
        "groq_available": groq_agent.is_available,
        "api_key_set": bool(os.getenv("GROQ_API_KEY"))
    }

