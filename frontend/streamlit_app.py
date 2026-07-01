import streamlit as st
import requests
import uuid
from datetime import datetime
import tempfile
import os
import pyotp
import qrcode
from io import BytesIO

st.set_page_config(page_title="Aiko Bank", page_icon="🏦", layout="wide")

# Custom CSS: Red and Black theme
st.markdown("""
<style>
    :root {
        --aiko-red: #dc2626;
        --aiko-red-glow: rgba(220, 38, 38, 0.4);
        --aiko-black: #111111;
        --aiko-dark: #1a1a1a;
        --aiko-gray: #2a2a2a;
        --aiko-text: #e5e5e5;
        --aiko-border: #333333;
    }
    
    .stApp {
        background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
    }
    
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    .stAppDeployButton {
        display: none;
    }
    
    .balance-card {
        background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
        padding: 1.25rem;
        border-radius: 12px;
        margin-bottom: 1rem;
        border: 1px solid #dc2626;
        box-shadow: 0 0 15px rgba(220, 38, 38, 0.15);
    }
    
    .balance-title {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #dc2626;
        margin-bottom: 0.5rem;
    }
    
    .balance-amount {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
        box-shadow: 0 2px 10px rgba(220, 38, 38, 0.3);
        width: 100%;
    }
    
    .stButton button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 20px rgba(220, 38, 38, 0.5);
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    .stTextInput input, .stTextArea textarea {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 8px;
        color: #ffffff;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #dc2626;
        box-shadow: 0 0 10px rgba(220, 38, 38, 0.3);
    }
    
    .login-container {
        background: rgba(26, 26, 26, 0.85);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(220, 38, 38, 0.3);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
    }
    
    .login-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    
    .divider {
        border-top: 1px solid #333333;
        margin: 1rem 0;
    }
    
    /* Floating Action Button */
    .fab-container {
        position: fixed;
        bottom: 80px;
        left: 20px;
        z-index: 1000;
    }
    
    .fab-button {
        width: 56px;
        height: 56px;
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        box-shadow: 0 4px 20px rgba(220, 38, 38, 0.5);
        transition: all 0.3s ease;
        border: none;
    }
    
    .fab-button:hover {
        transform: scale(1.1);
        box-shadow: 0 6px 25px rgba(220, 38, 38, 0.7);
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
    }
    
    .fab-button span {
        color: white;
        font-size: 24px;
        font-weight: bold;
    }
    
    .fab-tooltip {
        position: absolute;
        left: 65px;
        top: 50%;
        transform: translateY(-50%);
        background: #1a1a1a;
        color: #dc2626;
        padding: 0.5rem 1rem;
        border-radius: 8px;
        font-size: 0.75rem;
        white-space: nowrap;
        border: 1px solid #dc2626;
        opacity: 0;
        visibility: hidden;
        transition: all 0.3s ease;
        pointer-events: none;
    }
    
    .fab-container:hover .fab-tooltip {
        opacity: 1;
        visibility: visible;
    }
    
    /* Chat container for assistant */
    .assistant-chat-container {
        position: fixed;
        bottom: 150px;
        left: 20px;
        width: 320px;
        background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%);
        border-radius: 12px;
        border: 1px solid #dc2626;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        z-index: 1001;
        display: none;
        overflow: hidden;
    }
    
    .assistant-chat-container.show {
        display: block;
    }
    
    .assistant-header {
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        padding: 0.75rem 1rem;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .assistant-header-close {
        cursor: pointer;
        font-size: 1.2rem;
        font-weight: bold;
    }
    
    .assistant-messages {
        height: 300px;
        overflow-y: auto;
        padding: 0.75rem;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
    }
    
    .assistant-message {
        background: #2a2a2a;
        padding: 0.5rem 0.75rem;
        border-radius: 8px;
        font-size: 0.8rem;
        color: #e5e5e5;
        margin-bottom: 0.25rem;
        max-width: 85%;
    }
    
    .assistant-message.user {
        background: #dc2626;
        margin-left: auto;
        color: white;
    }
    
    .assistant-message.bot {
        background: #1a1a1a;
        border: 1px solid #dc2626;
        margin-right: auto;
    }
    
    .assistant-input-container {
        padding: 0.75rem;
        border-top: 1px solid #333333;
        display: flex;
        gap: 0.5rem;
    }
    
    .assistant-input {
        flex: 1;
        padding: 0.5rem;
        background: #2a2a2a;
        border: 1px solid #dc2626;
        border-radius: 8px;
        color: white;
        font-size: 0.8rem;
    }
    
    .assistant-send {
        background: #dc2626;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        color: white;
        cursor: pointer;
        font-size: 0.8rem;
    }
    
    .assistant-send:hover {
        background: #b91c1c;
    }
    
    /* Glow Footer */
    .glow-footer {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        text-align: center;
        padding: 0.75rem;
        background: linear-gradient(135deg, #0a0a0a 0%, #111111 100%);
        border-top: 1px solid rgba(220, 38, 38, 0.3);
        font-size: 0.7rem;
        color: #888888;
        letter-spacing: 0.5px;
        z-index: 100;
        box-shadow: 0 -2px 20px rgba(220, 38, 38, 0.1);
    }
    
    .glow-footer .copyright {
        color: #dc2626;
        font-weight: 500;
        text-shadow: 0 0 5px rgba(220, 38, 38, 0.5);
    }
    
    .sidebar-section {
        background: #0d0d0d;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid #2a2a2a;
    }
    
    .sidebar-title {
        font-size: 0.7rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #dc2626;
        margin-bottom: 1rem;
    }
    
    .user-detail {
        font-size: 0.8rem;
        color: #888888;
        margin-bottom: 0.25rem;
    }
    
    .user-detail strong {
        color: #dc2626;
        font-weight: 500;
    }
    
    .status-online {
        display: inline-block;
        width: 8px;
        height: 8px;
        background-color: #dc2626;
        border-radius: 50%;
        box-shadow: 0 0 5px #dc2626;
        margin-right: 0.5rem;
    }
    
    .info-text {
        font-size: 0.75rem;
        color: #666666;
    }
    
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #dc2626;
        border-radius: 3px;
    }
    
    .stChatMessage {
        background-color: #1a1a1a;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    section[data-testid="stSidebar"] {
        display: none;
    }
    
    /* Profile button styling */
    div[data-testid="column"] button {
        width: 48px !important;
        height: 48px !important;
        border-radius: 50% !important;
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        padding: 0 !important;
        margin-left: auto !important;
        display: block !important;
    }

    /* Upload section styling */
    .upload-section {
        background: #0d0d0d;
        border: 1px dashed #dc2626;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .upload-section .stFileUploader {
        background: transparent;
    }
    
    .agent-badge {
        display: inline-block;
        background: #dc2626;
        color: white;
        font-size: 0.6rem;
        padding: 0.15rem 0.5rem;
        border-radius: 10px;
        margin-right: 0.25rem;
    }
    
    .mfa-setup-container {
        background: rgba(26, 26, 26, 0.85);
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 16px;
        border: 1px solid rgba(220, 38, 38, 0.3);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def load_login_background():
    background_path = "login_background.webp"
    if os.path.exists(background_path):
        import base64
        with open(background_path, "rb") as f:
            bg_data = base64.b64encode(f.read()).decode()
        return f"url(data:image/webp;base64,{bg_data})"
    return None

login_bg = load_login_background()
if login_bg:
    st.markdown(f"""
    <style>
        div[data-testid="stAppViewContainer"] > section[data-testid="stHeader"] {{
            background: transparent;
        }}
        div[data-testid="stAppViewContainer"] {{
            background: linear-gradient(rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.8)), url({login_bg});
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
    </style>
    """, unsafe_allow_html=True)

glow_footer = """
<div class="glow-footer">
    <span>Copyright</span> <span class="copyright">© 2026 Aiko Bank</span>
    <span style="margin: 0 0.5rem;">|</span>
    <span>All rights reserved</span>
</div>
"""

# Floating Action Button HTML
fab_button = """
<div class="fab-container">
    <div class="fab-button" id="assistantFab">
        <span>💬</span>
    </div>
    <div class="fab-tooltip">Connect to Real-time Assistant</div>
</div>
"""

# Assistant Chat Window HTML
assistant_chat_window = """
<div id="assistantChat" class="assistant-chat-container">
    <div class="assistant-header">
        <span>Real-time Assistant</span>
        <span class="assistant-header-close" onclick="document.getElementById('assistantChat').classList.remove('show')">×</span>
    </div>
    <div id="assistantMessages" class="assistant-messages">
        <div class="assistant-message bot">Hello! I am your real-time assistant. How can I help you today?</div>
    </div>
    <div class="assistant-input-container">
        <input type="text" id="assistantInput" class="assistant-input" placeholder="Type your message..." onkeypress="if(event.key==='Enter') sendAssistantMessage()">
        <button class="assistant-send" onclick="sendAssistantMessage()">Send</button>
    </div>
</div>

<script>
    let isOpen = false;
    
    function toggleAssistant() {
        const chat = document.getElementById('assistantChat');
        if (chat.classList.contains('show')) {
            chat.classList.remove('show');
        } else {
            chat.classList.add('show');
        }
    }
    
    function sendAssistantMessage() {
        const input = document.getElementById('assistantInput');
        const message = input.value.trim();
        if (!message) return;
        
        const messagesContainer = document.getElementById('assistantMessages');
        
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'assistant-message user';
        userMsgDiv.textContent = message;
        messagesContainer.appendChild(userMsgDiv);
        
        input.value = '';
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        setTimeout(() => {
            const botMsgDiv = document.createElement('div');
            botMsgDiv.className = 'assistant-message bot';
            const responses = [
                "Thank you for reaching out. One of our representatives will assist you shortly.",
                "I understand your concern. Please allow me a moment to connect you with the right team.",
                "Thank you for your patience. Your query has been noted. A support agent will respond soon.",
                "I appreciate your message. Please provide your account details and we'll look into this.",
                "Thank you for contacting Aiko Bank support. How may I assist you further?"
            ];
            botMsgDiv.textContent = responses[Math.floor(Math.random() * responses.length)];
            messagesContainer.appendChild(botMsgDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 1000);
    }
    
    document.getElementById('assistantFab').onclick = toggleAssistant;
</script>
"""

# Helper function to generate MFA QR code
def generate_mfa_qr(username, secret):
    uri = pyotp.TOTP(secret).provisioning_uri(
        name=username,
        issuer_name="Aiko Bank"
    )

    qr = qrcode.make(uri)

    return qr.get_image()


def init_session_state():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "user_id" not in st.session_state:
        st.session_state.user_id = None
    if "user_info" not in st.session_state:
        st.session_state.user_info = None
    if "session_id" not in st.session_state:
        st.session_state.session_id = None
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None
    if "show_profile" not in st.session_state:
        st.session_state.show_profile = False
    if "has_documents" not in st.session_state:
        st.session_state.has_documents = False
    if "uploaded_files" not in st.session_state:
        st.session_state.uploaded_files = []
    if "agents_used" not in st.session_state:
        st.session_state.agents_used = []
    # New session state variables for upload status
    if "upload_status" not in st.session_state:
        st.session_state.upload_status = None
    if "upload_status_type" not in st.session_state:
        st.session_state.upload_status_type = None
    # MFA session state variables
    if "mfa_required" not in st.session_state:
        st.session_state.mfa_required = False
    if "pending_user_id" not in st.session_state:
        st.session_state.pending_user_id = None
    if "access_token" not in st.session_state:
        st.session_state.access_token = None
    if "refresh_token" not in st.session_state:
        st.session_state.refresh_token = None
    if "mfa_secret" not in st.session_state:
        st.session_state.mfa_secret = None
    if "mfa_username" not in st.session_state:
        st.session_state.mfa_username = None
    if "mfa_qr_generated" not in st.session_state:
        st.session_state.mfa_qr_generated = False

def fetch_user_profile(user_id, api_url):
    try:
        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
        
        response = requests.get(
            f"{api_url}/user/{user_id}",
            headers=headers,
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data["user"]

    except Exception as e:
        print(f"Profile fetch error: {e}")

    return None

def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_info = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.pending_query = None
    st.session_state.show_profile = False
    st.session_state.has_documents = False
    st.session_state.uploaded_files = []
    st.session_state.upload_status = None
    st.session_state.upload_status_type = None
    st.session_state.mfa_required = False
    st.session_state.pending_user_id = None
    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.mfa_secret = None
    st.session_state.mfa_username = None
    st.session_state.mfa_qr_generated = False
    st.rerun()

def send_message_and_get_response(message, user_id, api_url, has_documents=False):

    st.session_state.messages.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().strftime("%H:%M")
    })

    try:

        print("\n======================================")
        print("FRONTEND REQUEST")
        print("API URL:", api_url)
        print("USER ID:", user_id)
        print("MESSAGE:", message)
        print("HAS DOCUMENTS:", has_documents)
        print("======================================\n")

        headers = {}
        if st.session_state.access_token:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"

        response = requests.post(
            f"{api_url}/chat",
            json={
                "user_id": user_id,
                "message": message,
                "has_documents": has_documents
            },
            headers=headers,
            timeout=60
        )

        print("\n======================================")
        print("STATUS CODE:", response.status_code)
        print("RESPONSE TEXT:")
        print(response.text)
        print("======================================\n")

        if response.status_code == 200:

            data = response.json()

            bot_response = data.get(
                "response",
                "No response returned"
            )

            agents_used = data.get(
                "agents_used",
                []
            )

            st.session_state.messages.append({
                "role": "assistant",
                "content": bot_response,
                "timestamp": datetime.now().strftime("%H:%M")
            })

            st.session_state.agents_used = agents_used

            if "statement" in message.lower():

                statement_response = requests.post(
                    f"{api_url}/statement",
                    json={
                        "user_id": user_id,
                        "message": message
                    },
                    headers=headers,
                    timeout=60
                )

                if statement_response.status_code == 200:

                    pdf_content = statement_response.content

                    filename = (
                        f"statement_{user_id}_"
                        f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                    )

                    with tempfile.NamedTemporaryFile(
                        delete=False,
                        suffix=".pdf"
                    ) as tmp:

                        tmp.write(pdf_content)
                        tmp_path = tmp.name

                    st.session_state.pending_pdf = (
                        tmp_path,
                        filename
                    )

        elif response.status_code == 429:

            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    "Daily interaction limit reached. "
                    "Please try again tomorrow."
                ),
                "timestamp": datetime.now().strftime("%H:%M")
            })

        else:

            st.session_state.messages.append({
                "role": "assistant",
                "content": (
                    f"Backend Error {response.status_code}\n\n"
                    f"{response.text}"
                ),
                "timestamp": datetime.now().strftime("%H:%M")
            })

    except Exception as e:

        print("\n======================================")
        print("FRONTEND EXCEPTION")
        print(type(e))
        print(str(e))
        print("======================================\n")

        st.session_state.messages.append({
            "role": "assistant",
            "content": (
                f"Connection Error:\n\n{str(e)}"
            ),
            "timestamp": datetime.now().strftime("%H:%M")
        })

    st.rerun()

def render_header():
    # Safely get initial with fallback
    name = st.session_state.user_info.get("name", "User") if st.session_state.user_info else "User"
    initial = name[0].upper() if name else "U"
    
    st.markdown('''
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 0.75rem; border-bottom: 1px solid #333333; margin-bottom: 1.5rem;">
        <div style="flex: 1; text-align: left;">
            <h1 style="font-size: 1.8rem; font-weight: 700; background: linear-gradient(135deg, #ffffff 0%, #dc2626 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">Aiko Bank</h1>
        </div>
        <div style="flex: 2; text-align: center;">
            <p style="font-size: 0.85rem; color: #dc2626; font-style: italic; margin: 0;">Life's got 99 problems but banking ain't 1</p>
        </div>
        <div style="flex: 1; text-align: right;">
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([4, 1, 1])
    with col3:
        profile_clicked = st.button(f"{initial}", key="profile_btn")
        if profile_clicked:
            st.session_state.show_profile = not st.session_state.show_profile
            st.rerun()

def show_profile_modal():
    if st.session_state.get("show_profile", False) and st.session_state.user_info:
        # Safely get user info with fallbacks
        name = st.session_state.user_info.get('name', 'User')
        credit_score = st.session_state.user_info.get('credit_score', 'N/A')
        user_id = st.session_state.user_id or 'N/A'
        email = st.session_state.user_info.get('email', 'N/A')
        
        st.markdown(f'''
        <div style="position: fixed; top: 80px; right: 20px; width: 280px; background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); border-radius: 12px; border: 1px solid #dc2626; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5); padding: 1rem; z-index: 1000;">
            <div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem; border-bottom: 1px solid #333333; padding-bottom: 0.5rem;">{name}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.3rem;"><strong>Credit Score:</strong> {credit_score}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.3rem;"><strong>ID:</strong> {user_id}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.8rem;"><strong>Email:</strong> {email}</div>
        </div>
        ''', unsafe_allow_html=True)

def login_page():
    API_URL = "http://127.0.0.1:8000"

    # MFA OTP Screen - Check at the very top of login_page()
    if st.session_state.mfa_required:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.markdown(
                '<div class="login-title">🔐 Two-Factor Authentication</div>',
                unsafe_allow_html=True
            )

            # Check if we have MFA secret for setup
            if st.session_state.mfa_secret and not st.session_state.mfa_qr_generated:
                # Show setup button
                if st.button(
                    "📱 Setup Google Authenticator",
                    use_container_width=True,
                    key="setup_mfa_btn"
                ):
                    st.session_state.mfa_qr_generated = True
                    st.rerun()
                
                st.markdown("""
                <div style="text-align:center;margin-top:1rem;color:#888888;font-size:0.85rem;">
                    Click the button above to set up your authenticator app.
                </div>
                """, unsafe_allow_html=True)
            
            # Show QR code and instructions if generated
            if st.session_state.mfa_qr_generated and st.session_state.mfa_secret:
                # Generate QR code
                qr = generate_mfa_qr(
                    st.session_state.mfa_username,
                    st.session_state.mfa_secret
                )
                
                # Display QR code
                st.image(
                    qr,
                    caption="Scan with Google Authenticator",
                    use_column_width=True
                )
                
                st.info(
                    """
                    **Setup Instructions:**
                    1. Open Google Authenticator
                    2. Tap the + icon
                    3. Scan the QR code above
                    4. Enter the 6-digit code below to verify
                    """
                )
                
                st.markdown("---")
            
            # OTP input
            otp = st.text_input(
                "Enter Verification Code",
                placeholder="Enter 6-digit code from Google Authenticator",
                key="mfa_otp",
                label_visibility="collapsed",
                max_chars=6
            )

            # Verify button - always show
            if st.button(
                "Verify OTP",
                use_container_width=True,
                key="verify_otp_btn"
            ):
                if otp and len(otp) == 6:
                    try:
                        response = requests.post(
                            f"{API_URL}/verify-otp",
                            json={
                                "user_id": st.session_state.pending_user_id,
                                "otp": otp
                            },
                            timeout=30
                        )

                        if response.status_code == 200:
                            data = response.json()
                            
                            access_token = data.get("access_token")
                            user_id = data.get("user_id")
                            
                            if access_token and user_id:
                                st.session_state.access_token = access_token
                                st.session_state.refresh_token = data.get("refresh_token")
                                
                                profile = fetch_user_profile(user_id, API_URL)
                                
                                if profile is None:
                                    st.error("Could not fetch user profile from backend.")
                                else:
                                    st.session_state.authenticated = True
                                    st.session_state.user_id = user_id
                                    st.session_state.user_info = profile
                                    st.session_state.session_id = str(uuid.uuid4())
                                    st.session_state.messages = []
                                    st.session_state.agents_used = []
                                    
                                    # Clear MFA state
                                    st.session_state.mfa_required = False
                                    st.session_state.pending_user_id = None
                                    st.session_state.mfa_secret = None
                                    st.session_state.mfa_username = None
                                    st.session_state.mfa_qr_generated = False

                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": (
                                            f"Welcome, {profile['name']}. "
                                            f"Your banking assistant is ready. "
                                            f"How may I assist you today?"
                                        ),
                                        "timestamp": datetime.now().strftime("%H:%M")
                                    })

                                    st.rerun()
                            else:
                                st.error("Invalid response from server. Missing access_token or user_id.")

                        else:
                            st.error("Invalid OTP. Please try again.")

                    except requests.exceptions.ConnectionError:
                        st.error("Cannot connect to the server. Please ensure the backend is running.")
                    except Exception as e:
                        st.error(f"An error occurred: {str(e)}")

                else:
                    st.warning("Please enter a valid 6-digit verification code.")

            if st.button(
                "← Back to Login",
                use_container_width=True,
                key="back_to_login_btn"
            ):
                st.session_state.mfa_required = False
                st.session_state.pending_user_id = None
                st.session_state.mfa_secret = None
                st.session_state.mfa_username = None
                st.session_state.mfa_qr_generated = False
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown(glow_footer, unsafe_allow_html=True)
        return  # Exit login_page early, don't show regular login form

    # Regular login form (only shown when mfa_required is False)
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:

        st.markdown(
            '<div class="login-container">',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="login-title">Aiko Bank</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '''
            <div style="text-align:center;margin-bottom:1rem;">
                <p style="font-size:0.85rem;color:#dc2626;font-style:italic;">
                    Life's got 99 problems but banking ain't 1
                </p>
            </div>
            ''',
            unsafe_allow_html=True
        )

        username = st.text_input(
            "Username",
            placeholder="Enter your username",
            key="login_username",
            label_visibility="collapsed"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            key="login_password",
            label_visibility="collapsed"
        )

        if st.button(
            "Sign In",
            use_container_width=True,
            key="signin_btn"
        ):

            if username and password:

                try:
                    login_response = requests.post(
                        f"{API_URL}/login",
                        json={
                            "username": username,
                            "password": password
                        },
                        timeout=30
                    )

                    if login_response.status_code == 200:
                        data = login_response.json()

                        # Check if MFA is required
                        if data.get("mfa_required"):
                            st.session_state.mfa_required = True
                            st.session_state.pending_user_id = data.get("user_id")
                            
                            # Store MFA secret and username for QR generation
                            st.session_state.mfa_secret = data.get("totp_secret")
                            st.session_state.mfa_username = data.get("username")
                            st.session_state.mfa_qr_generated = False
                            
                            st.rerun()
                        else:
                            # No MFA required - proceed with login
                            user_id = data.get("user_id")
                            access_token = data.get("access_token")
                            
                            if user_id and access_token:
                                st.session_state.access_token = access_token
                                st.session_state.refresh_token = data.get("refresh_token")
                                
                                profile = fetch_user_profile(user_id, API_URL)
                                if profile is None:
                                    st.error("Could not fetch user profile from backend.")
                                else:
                                    st.session_state.authenticated = True
                                    st.session_state.user_id = user_id
                                    st.session_state.user_info = profile
                                    st.session_state.session_id = str(uuid.uuid4())
                                    st.session_state.messages = []
                                    st.session_state.agents_used = []

                                    st.session_state.messages.append({
                                        "role": "assistant",
                                        "content": (
                                            f"Welcome, {profile['name']}. "
                                            f"Your banking assistant is ready. "
                                            f"How may I assist you today?"
                                        ),
                                        "timestamp": datetime.now().strftime("%H:%M")
                                    })

                                    st.rerun()
                            else:
                                st.error("Invalid response from server. Missing user_id or access_token.")

                    else:
                        st.error(f"Login failed: {login_response.status_code} - {login_response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to the server. Please ensure the backend is running.")
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

            else:
                st.warning("Please enter your credentials.")

        st.markdown(
            '''
            <div class="info-text"
                 style="text-align:center;margin-top:1rem;">
                 24/7 Secure Banking Assistant
            </div>
            ''',
            unsafe_allow_html=True
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True
        )

    st.markdown(
        glow_footer,
        unsafe_allow_html=True
    )

def main_app():
    API_URL = "http://127.0.0.1:8000"
    
    render_header()
    show_profile_modal()
    
    with st.sidebar:
        if st.button("Sign Out", key="sidebar_signout", use_container_width=True):
            logout()
    
    chat_col1, chat_col2 = st.columns([3, 1])
    
    with chat_col1:
        st.markdown("### 💬 Banking Assistant")
        st.caption("Ask anything - finance, travel, health, legal, document analysis...")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
        
        # Show agents used if available
        if st.session_state.agents_used and len(st.session_state.messages) > 0:
            agents_text = " " + " | ".join([f"<span class='agent-badge'>{a}</span>" for a in st.session_state.agents_used])
            st.markdown(f'<div style="font-size: 0.7rem; color: #666; margin-top: -0.5rem; margin-bottom: 0.5rem;">{agents_text}</div>', unsafe_allow_html=True)
        
        if hasattr(st.session_state, 'pending_pdf') and st.session_state.pending_pdf:
            tmp_path, filename = st.session_state.pending_pdf
            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="📄 Download Statement PDF",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
            st.session_state.pending_pdf = None
        
        if prompt := st.chat_input("Ask anything..."):
            send_message_and_get_response(
                prompt,
                st.session_state.user_id,
                API_URL,
                st.session_state.has_documents
            )
    
    with chat_col2:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">📎 Document Upload</div>', unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            "Upload any document",
            type=['pdf', 'docx', 'txt', 'xlsx', 'csv', 'png', 'jpg', 'jpeg'],
            key="doc_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded_file:
            if st.button("Process Document", use_container_width=True):
                with st.spinner("Processing document..."):
                    files = {"file": uploaded_file}
                    try:
                        headers = {}
                        if st.session_state.access_token:
                            headers["Authorization"] = f"Bearer {st.session_state.access_token}"
                        
                        response = requests.post(
                            f"{API_URL}/upload?user_id={st.session_state.user_id}",
                            files=files,
                            headers=headers,
                            timeout=60
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if data.get("success"):
                                st.session_state.upload_status_type = "success"
                                st.session_state.upload_status = "Document processed successfully."
                                
                                st.session_state.has_documents = True
                                
                                if uploaded_file.name not in st.session_state.uploaded_files:
                                    st.session_state.uploaded_files.append(uploaded_file.name)
                            else:
                                st.session_state.upload_status_type = "error"
                                st.session_state.upload_status = (
                                    "Invalid financial documents found.\n\n"
                                    "Please upload relevant financial document to get started."
                                )
                                
                                st.session_state.has_documents = False
                            
                            st.rerun()
                        else:
                            st.session_state.upload_status_type = "error"
                            st.session_state.upload_status = f"Failed to process document: {response.text}"
                            st.rerun()
                    except Exception as e:
                        st.session_state.upload_status_type = "error"
                        st.session_state.upload_status = f"Connection error: {e}"
                        st.rerun()
        
        # Display upload status messages below the button
        if st.session_state.upload_status:
            if st.session_state.upload_status_type == "success":
                st.success(st.session_state.upload_status)
            else:
                st.error(st.session_state.upload_status)
        
        if st.session_state.uploaded_files:
            st.markdown('<div style="margin-top: 0.75rem;"><div class="sidebar-title">📄 Uploaded Documents</div></div>', unsafe_allow_html=True)
            for f in st.session_state.uploaded_files:
                st.markdown(f'<div style="font-size: 0.75rem; color: #e5e5e5; padding: 0.25rem 0;">• {f}</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">💰 Account Snapshot</div>', unsafe_allow_html=True)
        
        # Safely get balances with fallback
        savings_balance = st.session_state.user_info.get('savings_balance', 0) if st.session_state.user_info else 0
        checking_balance = st.session_state.user_info.get('checking_balance', 0) if st.session_state.user_info else 0
        
        st.markdown(f'''
        <div class="balance-card">
            <div class="balance-title">Savings Account</div>
            <div class="balance-amount">₹{savings_balance:,.2f}</div>
        </div>
        <div class="balance-card">
            <div class="balance-title">Checking Account</div>
            <div class="balance-amount">₹{checking_balance:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">⚡ Quick Actions</div>', unsafe_allow_html=True)
        
        actions = [
            ("Check Balance", "What is my account balance?"),
            ("Get Statement", "Show my last month statement"),
            ("Personal Loan", "personal loan"),
            ("Loan Eligibility", "check eligibility"),
            ("EMI Calculator", "emi for 50000"),
            ("Travel Plan", "Plan a trip to Japan for 20 days"),
            ("Analyze Document", "Analyze this document" + (" (upload first)" if not st.session_state.uploaded_files else ""))
        ]
        
        for label, query in actions:
            if st.button(label, key=f"action_{label}", use_container_width=True):
                send_message_and_get_response(
                    query,
                    st.session_state.user_id,
                    API_URL,
                    st.session_state.has_documents
                )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title"> Session Information</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="user-detail"><span class="status-online"></span> Active Session</div>
        <div class="user-detail">ID: {st.session_state.session_id[:8] if st.session_state.session_id else 'N/A'}...</div>
        <div class="user-detail">Messages: {len(st.session_state.messages)}</div>
        <div class="user-detail" style="margin-top: 0.5rem; color: #dc2626;">Agentic AI v2.0</div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(fab_button, unsafe_allow_html=True)
    st.markdown(assistant_chat_window, unsafe_allow_html=True)
    
    st.markdown(glow_footer, unsafe_allow_html=True)

init_session_state()

if not st.session_state.authenticated:
    login_page()
else:
    main_app()