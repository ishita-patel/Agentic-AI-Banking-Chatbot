# backend/main.py

from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

import uuid
import os
import shutil

load_dotenv()

print("MAIN.PY LOADED")

from backend.orchestrator.orchestrator import Orchestrator
from backend.data_loader import BankDataLoader

app = FastAPI(
    title="Agentic Bank Multi-Agent System"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# SERVICES
# ============================================================

orchestrator = Orchestrator()
data_loader = BankDataLoader()

# ============================================================
# MODELS
# ============================================================

class ChatRequest(BaseModel):
    user_id: str
    message: str
    has_documents: bool = False


class ChatResponse(BaseModel):
    session_id: str
    response: str
    analysis: dict
    agents_used: list
    timestamp: datetime


# ============================================================
# ROOT
# ============================================================

@app.get("/")
async def root():
    return {
        "status": "running",
        "system": "Agentic Bank Multi-Agent"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now()
    }


# ============================================================
# USER PROFILE
# ============================================================

@app.get("/user/{user_id}")
async def get_user_profile(user_id: str):

    try:

        user = data_loader.get_user(user_id)

        if not user:
            return {
                "success": False,
                "message": "User not found"
            }

        return {
            "success": True,
            "user": {
                "user_id": user.get("user_id"),
                "name": user.get("name"),
                "email": user.get("email", ""),
                "phone": user.get("phone", ""),
                "city": user.get("city", ""),
                "pincode": user.get("pincode", ""),
                "credit_score": user.get("credit_score", 0),
                "loan_eligible": user.get(
                    "loan_eligible",
                    False
                ),
                "account_age_years": user.get(
                    "account_age_years",
                    0
                ),
                "savings_balance": user.get(
                    "accounts",
                    {}
                ).get(
                    "savings",
                    {}
                ).get(
                    "balance",
                    0
                ),
                "checking_balance": user.get(
                    "accounts",
                    {}
                ).get(
                    "checking",
                    {}
                ).get(
                    "balance",
                    0
                ),
                "monthly_income": user.get(
                    "employment",
                    {}
                ).get(
                    "monthly_income",
                    0
                )
            }
        }

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# CHAT
# ============================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):

    try:

        result = await orchestrator.process(
            user_id=request.user_id,
            query=request.message,
            has_documents=request.has_documents
        )

        return ChatResponse(
            session_id=str(uuid.uuid4()),
            response=result.get(
                "response",
                "No response generated."
            ),
            analysis=result.get(
                "analysis",
                {}
            ),
            agents_used=result.get(
                "agents_used",
                []
            ),
            timestamp=datetime.now()
        )

    except Exception as e:

        return ChatResponse(
            session_id=str(uuid.uuid4()),
            response=f"Error: {str(e)}",
            analysis={},
            agents_used=["error"],
            timestamp=datetime.now()
        )


# ============================================================
# DOCUMENT UPLOAD
# ============================================================

@app.post("/upload")
async def upload_document(
    user_id: str,
    file: UploadFile = File(...)
):

    upload_dir = f"uploads/{user_id}"

    os.makedirs(
        upload_dir,
        exist_ok=True
    )

    file_path = os.path.join(
        upload_dir,
        file.filename
    )

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer
        )

    try:

        result = await orchestrator.upload_document(
            user_id,
            file_path
        )

        return result

    except Exception as e:

        return {
            "success": False,
            "message": str(e)
        }


# ============================================================
# DEBUG
# ============================================================

@app.get("/agents")
async def get_agents():

    return {
        "available_agents":
        orchestrator.get_available_agents()
    }


@app.get("/status")
async def get_status():

    return {
        "agent_status":
        orchestrator.get_agent_status()
    }