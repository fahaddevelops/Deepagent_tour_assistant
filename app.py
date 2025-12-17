
import streamlit as st
import requests
import json
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage

# ----------------------------------------------------------------------
# Page Config
# ----------------------------------------------------------------------
load_dotenv()

st.set_page_config(
    page_title="Deep Agent Tour Planner",
    page_icon="✈️",
    layout="wide",
)

# ----------------------------------------------------------------------
# CSS for Aesthetics
# ----------------------------------------------------------------------
st.markdown("""
<style>
    .reportview-container {
        background: #f0f2f6;
    }
    .main-header {
        font-family: 'Helvetica Neue', sans-serif;
        color: #333;
    }
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
    }
    .chat-message {
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
    }
    .chat-message.user {
        background-color: #2b313e;
        color: #ffffff;
    }
    .chat-message.bot {
        background-color: #f0f2f6;
        color: #000000;
        border: 1px solid #e0e0e0;
    }
    .log-message {
        font-family: monospace;
        font-size: 0.85em;
        color: #555;
        border-left: 2px solid #ddd;
        padding-left: 10px;
        margin: 5px 0;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------
# Session State
# ----------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ----------------------------------------------------------------------
# Sidebar
# ----------------------------------------------------------------------
with st.sidebar:
    st.title("🌏 Plan Your Journey")
    st.markdown("Configure your specific preferences below")
    
    country = st.selectbox(
        "Select Country (Asia)",
        ["Japan", "Thailand", "Vietnam", "India", "Indonesia", "South Korea", "China", "Other"]
    )
    
    if country == "Other":
        country = st.text_input("Enter Country Name")
        
    city = st.text_input("City or Tour Points", placeholder="e.g., Kyoto, Phuket, Golden Triangle")
    
    budget = st.select_slider(
        "Budget / Price Selection",
        options=["Budget (Backpacker)", "Standard (Comfort)", "Luxury (Premium)"],
        value="Standard (Comfort)"
    )
    
    additional_notes = st.text_area("Additional Requirements", placeholder="Vegetarian food, family friendly, etc.")
    
    start_btn = st.button("Start Planning 🚀")
    
    st.divider()
    api_base = os.getenv("API_BASE", "http://localhost:8000")
    try:
        r = requests.get(f"{api_base}/health", timeout=1.5)
        if r.status_code == 200:
            st.caption(f"Backend Status: Online at {api_base}")
        else:
            st.caption(f"Backend Status: {r.status_code} at {api_base}")
    except Exception:
        st.caption(f"Backend Status: Offline at {api_base}")

# ----------------------------------------------------------------------
# Main Logic
# ----------------------------------------------------------------------
st.title("✈️ Deep Tour Agent")
st.markdown(f"**Target**: {city if city else '...'}, {country} | **Style**: {budget}")

# Display Chat History
for msg in st.session_state.messages:
    if isinstance(msg, HumanMessage):
        with st.chat_message("user"):
            st.write(msg.content)
    elif isinstance(msg, AIMessage):
        with st.chat_message("assistant"):
            st.write(msg.content)

def run_agent_via_api():
    # Helper to convert session state messages to list of dicts
    api_messages = []
    for m in st.session_state.messages:
        role = "user" if isinstance(m, HumanMessage) else "assistant"
        api_messages.append({"role": role, "content": m.content})
    
    api_base = os.getenv("API_BASE", "http://localhost:8000")
    api_url = f"{api_base}/plan"
    
    with st.chat_message("assistant"):
        status_col, log_col = st.columns([1, 1])
        
        message_placeholder = st.empty()
        logs_placeholder = st.expander("🛠️ Planner Observability Logs", expanded=True)
        
        full_logs = []
        final_answer = ""
        
        try:
            # Send full history
            with requests.post(api_url, json={"messages": api_messages}, stream=True) as response:
                if response.status_code != 200:
                    st.error(f"API Error: {response.status_code} - {response.reason}")
                    return

                for line in response.iter_lines():
                    if line:
                        try:
                            data = json.loads(line)
                            msg_type = data.get("type")
                            
                            if msg_type == "log":
                                log_msg = data.get("message", "")
                                full_logs.append(log_msg)
                                with logs_placeholder:
                                    st.markdown(log_msg)
                                    
                            elif msg_type == "answer":
                                final_answer = data.get("content", "")
                                # accumulate answering if streaming chunks (future) or just set if block
                                message_placeholder.markdown(final_answer)
                                
                            elif msg_type == "error":
                                st.error(f"Backend Error: {data.get('message')}")
                                
                        except json.JSONDecodeError:
                            pass
        except requests.exceptions.ConnectionError:
            st.error("Could not connect to backend server. Is 'run_app.bat' running?")
            return

        if final_answer:
            st.session_state.messages.append(AIMessage(content=final_answer))

if start_btn:
    if not country or not city:
        st.error("Please provide at least a Country and City/Tour Point.")
    else:
        query = f"""
        Please plan a trip to {city}, {country}.
        Budget Level: {budget}.
        Additional Notes: {additional_notes}.
        """
        
        st.session_state.messages.append(HumanMessage(content=query))
        run_agent_via_api()

# ----------------------------------------------------------------------
# Chat Input (Human in the Loop)
# ----------------------------------------------------------------------
if st.session_state.messages:
    user_chat = st.chat_input("Ask changes or details...")
    if user_chat:
        st.session_state.messages.append(HumanMessage(content=user_chat))
        with st.chat_message("user"):
            st.write(user_chat)
        run_agent_via_api()
