import streamlit as st
import requests
import uuid
from datetime import datetime
import tempfile
import os

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
        
        // Add user message
        const userMsgDiv = document.createElement('div');
        userMsgDiv.className = 'assistant-message user';
        userMsgDiv.textContent = message;
        messagesContainer.appendChild(userMsgDiv);
        
        // Clear input
        input.value = '';
        
        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // Simulate bot response after delay
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

MOCK_USERS = {
    "aarav.sharma": {
        "password": "pass123",
        "user_id": "user_001",
        "name": "Aarav Sharma",
        "email": "aarav.sharma@aikobank.com",
        "phone": "+91 98765 43210",
        "account_type": "Premium Savings",
        "savings_balance": 352610.77,
        "checking_balance": 54578.84
    },
    "priya.singh": {
        "password": "pass123",
        "user_id": "user_002",
        "name": "Priya Singh",
        "email": "priya.singh@aikobank.com",
        "phone": "+91 98765 43211",
        "account_type": "Savings Plus",
        "savings_balance": 12750.45,
        "checking_balance": 3200.00
    },
    "amit.patel": {
        "password": "pass123",
        "user_id": "user_003",
        "name": "Amit Patel",
        "email": "amit.patel@aikobank.com",
        "phone": "+91 98765 43212",
        "account_type": "Corporate Account",
        "savings_balance": 87500.00,
        "checking_balance": 25000.00
    },
    "ishita.patel": {
        "password": "pass123",
        "user_id": "user_004",
        "name": "Ishita Patel",
        "email": "ishita.patel@aikobank.com",
        "phone": "+91 98765 43215",
        "account_type": "Premium Savings",
        "savings_balance": 425000.00,
        "checking_balance": 75000.00
    }
}

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

def authenticate_user(username, password):
    if username in MOCK_USERS and MOCK_USERS[username]["password"] == password:
        return MOCK_USERS[username]["user_id"], MOCK_USERS[username]
    return None, None

def logout():
    st.session_state.authenticated = False
    st.session_state.user_id = None
    st.session_state.user_info = None
    st.session_state.session_id = None
    st.session_state.messages = []
    st.session_state.pending_query = None
    st.session_state.show_profile = False
    st.rerun()

def send_message_and_get_response(message, user_id, api_url):
    st.session_state.messages.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().strftime("%H:%M")
    })
    
    try:
        response = requests.post(
            f"{api_url}/chat",
            json={"user_id": user_id, "message": message},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            bot_response = data["response"]
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": bot_response,
                "timestamp": datetime.now().strftime("%H:%M")
            })
            
            if "statement" in message.lower():
                statement_response = requests.post(
                    f"{api_url}/statement",
                    json={"user_id": user_id, "message": message}
                )
                if statement_response.status_code == 200:
                    pdf_content = statement_response.content
                    filename = f"statement_{user_id}_{datetime.now().strftime('%Y%m%d_H%M%S')}.pdf"
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(pdf_content)
                        tmp_path = tmp.name
                    st.session_state.pending_pdf = (tmp_path, filename)
        elif response.status_code == 429:
            st.session_state.messages.append({
                "role": "assistant",
                "content": "Daily interaction limit reached. Please try again tomorrow.",
                "timestamp": datetime.now().strftime("%H:%M")
            })
    except Exception:
        st.session_state.messages.append({
            "role": "assistant",
            "content": "Unable to connect to banking service. Please ensure the backend is running.",
            "timestamp": datetime.now().strftime("%H:%M")
        })
    
    st.rerun()

def render_header():
    initial = st.session_state.user_info['name'][0].upper()
    
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
    if st.session_state.get("show_profile", False):
        st.markdown(f'''
        <div style="position: fixed; top: 80px; right: 20px; width: 280px; background: linear-gradient(135deg, #1a1a1a 0%, #0d0d0d 100%); border-radius: 12px; border: 1px solid #dc2626; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5); padding: 1rem; z-index: 1000;">
            <div style="font-size: 1rem; font-weight: 600; color: #ffffff; margin-bottom: 0.5rem; border-bottom: 1px solid #333333; padding-bottom: 0.5rem;">{st.session_state.user_info['name']}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.3rem;"><strong>Account:</strong> {st.session_state.user_info['account_type']}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.3rem;"><strong>ID:</strong> {st.session_state.user_id}</div>
            <div style="font-size: 0.8rem; color: #888888; margin-bottom: 0.8rem;"><strong>Email:</strong> {st.session_state.user_info['email']}</div>
        </div>
        ''', unsafe_allow_html=True)

def login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Aiko Bank</div>', unsafe_allow_html=True)
        st.markdown('<div style="text-align: center; margin-bottom: 1rem;"><p style="font-size: 0.85rem; color: #dc2626; font-style: italic;">Life\'s got 99 problems but banking ain\'t 1</p></div>', unsafe_allow_html=True)
        
        username = st.text_input("Username", placeholder="Enter your username", key="login_username", label_visibility="collapsed")
        password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password", label_visibility="collapsed")
        
        if st.button("Sign In", use_container_width=True):
            if username and password:
                user_id, user_info = authenticate_user(username, password)
                if user_id:
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.user_info = user_info
                    st.session_state.session_id = str(uuid.uuid4())
                    st.session_state.messages = []
                    
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": f"Welcome, {user_info['name']}. Your banking assistant is ready. How may I assist you today?",
                        "timestamp": datetime.now().strftime("%H:%M")
                    })
                    st.rerun()
                else:
                    st.error("Invalid credentials. Please try again.")
            else:
                st.warning("Please enter your credentials.")
        
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        with st.expander("Demo Access"):
            st.markdown("""
            | Username | Password |
            |----------|----------|
            | aarav.sharma | pass123 |
            | priya.singh | pass123 |
            | amit.patel | pass123 |
            | ishita.patel | pass123 |
            """)
        
        st.markdown('<div class="info-text" style="text-align: center; margin-top: 1rem;">24/7 Secure Banking Assistant</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown(glow_footer, unsafe_allow_html=True)

def main_app():
    API_URL = "http://localhost:8000"
    
    render_header()
    show_profile_modal()
    
    with st.sidebar:
        if st.button("Sign Out", key="sidebar_signout", use_container_width=True):
            logout()
    
    chat_col1, chat_col2 = st.columns([3, 1])
    
    with chat_col1:
        st.markdown("### Banking Assistant")
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                st.caption(msg["timestamp"])
        
        if hasattr(st.session_state, 'pending_pdf') and st.session_state.pending_pdf:
            tmp_path, filename = st.session_state.pending_pdf
            with open(tmp_path, "rb") as f:
                st.download_button(
                    label="Download Statement PDF",
                    data=f,
                    file_name=filename,
                    mime="application/pdf"
                )
            st.session_state.pending_pdf = None
        
        if prompt := st.chat_input("How can I help you today?"):
            send_message_and_get_response(prompt, st.session_state.user_id, API_URL)
    
    with chat_col2:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">Account Snapshot</div>', unsafe_allow_html=True)
        
        st.markdown(f'''
        <div class="balance-card">
            <div class="balance-title">Savings Account</div>
            <div class="balance-amount">₹{st.session_state.user_info['savings_balance']:,.2f}</div>
        </div>
        <div class="balance-card">
            <div class="balance-title">Checking Account</div>
            <div class="balance-amount">₹{st.session_state.user_info['checking_balance']:,.2f}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">Quick Services</div>', unsafe_allow_html=True)
        
        actions = [
            ("Check Balance", "What is my account balance?"),
            ("Get Statement", "Show my last month statement"),
            ("Personal Loan", "personal loan"),
            ("Loan Eligibility", "check eligibility"),
            ("EMI Calculator", "emi for 50000")
        ]
        
        for label, query in actions:
            if st.button(label, key=f"action_{label}", use_container_width=True):
                send_message_and_get_response(query, st.session_state.user_id, API_URL)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-title">Session Information</div>', unsafe_allow_html=True)
        st.markdown(f'''
        <div class="user-detail"><span class="status-online"></span> Active Session</div>
        <div class="user-detail">ID: {st.session_state.session_id[:8] if st.session_state.session_id else 'N/A'}...</div>
        <div class="user-detail">Messages: {len(st.session_state.messages)}</div>
        <div class="user-detail" style="margin-top: 0.5rem;">Aiko Bank v1.0</div>
        ''', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Floating Action Button and Assistant Chat Window
    st.markdown(fab_button, unsafe_allow_html=True)
    st.markdown(assistant_chat_window, unsafe_allow_html=True)
    
    st.markdown(glow_footer, unsafe_allow_html=True)

init_session_state()

if not st.session_state.authenticated:
    login_page()
else:
    main_app()