from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv
import time
import uuid
import os
import shutil
import pyotp

load_dotenv()

print("SERVER TIME:", datetime.utcnow())
print("SERVER UNIX:", int(time.time()))
print("MAIN.PY LOADED")

# from backend.orchestrator.orchestrator import Orchestrator
from backend.data_loader import BankDataLoader
from backend.auth.auth_service import AuthService
from backend.auth.dependencies import get_current_user
from backend.auth.jwt_handler import create_access_token

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

#orchestrator = Orchestrator()
data_loader = BankDataLoader()
auth_service = AuthService()

# ============================================================
# MODELS
# ============================================================

class ChatRequest(BaseModel):
    message: str
    has_documents: bool = False


class ChatResponse(BaseModel):
    session_id: str
    response: str
    analysis: dict
    agents_used: list
    timestamp: datetime


class LoginRequest(BaseModel):
    username: str
    password: str


class OTPRequest(BaseModel):
    user_id: str
    otp: str


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
# AUTHENTICATION
# ============================================================

@app.post("/login")
async def login(request: LoginRequest):

    token = auth_service.login(
        request.username,
        request.password
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    user = auth_service.loader.get_user_by_username(
        request.username
    )

    # MFA enabled?  
    if user.get("mfa_enabled", False):
        return {
            "mfa_required": True,
            "user_id": user["user_id"],
            "username": user["username"],
            "totp_secret": user["totp_secret"]
        }

    return {
        "user_id": user["user_id"],
        "access_token": token,
        "token_type": "bearer"
    }


@app.post("/verify-otp")
async def verify_otp(
    request: OTPRequest
):

    user = data_loader.get_user(
        request.user_id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    secret = user.get("totp_secret")

    print("RAW SECRET REPR:", repr(secret))

    if not secret:
        raise HTTPException(
            status_code=400,
            detail="MFA not configured"
        )
    
    print("SERVER UTC:", datetime.utcnow())
    print("SERVER UNIX:", int(time.time()))
    print("DB SECRET:", secret)

    totp = pyotp.TOTP(secret)

    expected_otp = totp.now()

    verification_result = totp.verify(
        request.otp,
        valid_window=10
    )

    print("EXPECTED OTP:", expected_otp)
    print("RECEIVED OTP:", request.otp)
    print("VERIFY RESULT:", verification_result)

    if not verification_result:
        raise HTTPException(
            status_code=401,
            detail="Invalid OTP"
        )
    
    access_token = create_access_token(
        {
            "user_id":
            user["user_id"],

            "role":
            user.get(
                "role",
                "customer"
            )
        }
    )

    return {
        "user_id":
        user["user_id"],

        "access_token":
        access_token,

        "token_type":
        "bearer"
    }


# ============================================================
# USER PROFILE
# ============================================================

@app.get("/user/{user_id}")
async def get_user_profile(
    user_id: str,
    current_user = Depends(get_current_user)
):
    # Verify the user is accessing their own profile
    if current_user["user_id"] != user_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this user's profile"
        )

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

#@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user = Depends(get_current_user)
):
    try:
        result = await orchestrator.process(
            user_id=current_user["user_id"],
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

#@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)
):
    user_id = current_user["user_id"]
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

#@app.get("/agents")
async def get_agents(
    current_user = Depends(get_current_user)
):
    return {
        "available_agents":
        orchestrator.get_available_agents()
    }


#@app.get("/status")
async def get_status(
    current_user = Depends(get_current_user)
):
    return {
        "agent_status":
        orchestrator.get_agent_status()
    }