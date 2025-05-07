import streamlit as st
import requests
import json
from typing import Dict, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# GPT-Lab Configuration
GPTLAB_BASE_URL = "https://gptlab.rd.tuni.fi/GPT-Lab/resources/RANDOM/v1"
GPTLAB_API_KEY = "sk-ollama-gptlab-6cc87c9bd38b24aca0fe77f0c9c4d68d"

# Static list of available models (as provided)
MODEL_OPTIONS = [
    "llama3.2",
    "llama3.1:70b-instruct-q4_K_M",
    "codellama:7b",
    "codegemma:7b",
    "deepseek-coder:6.7b",
    "phi4:14b-fp16",
    "GPT-Lab/Viking-33B-cp2000B-GGUF:Q6_K",
    "magicoder:7b"
]

def gptlab_chat(prompt: str, model: str, temperature: float, max_tokens: int) -> str:
    try:
        headers = {
            "Authorization": f"Bearer {GPTLAB_API_KEY}",
            "Content-Type": "application/json"
        }
        response = requests.post(
            f"{GPTLAB_BASE_URL}/completions",
            headers=headers,
            json={
                "model": model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
        )
        if response.status_code == 404 and "not found" in response.text:
            return "[Model Not Available] This model is not available on the server. Please select a different model."
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and data["choices"]:
                return data["choices"][0].get("text", "")
            elif "response" in data:
                return data["response"]
            else:
                return str(data)
        else:
            return f"[Error {response.status_code}] {response.text}"
    except Exception as e:
        return f"[Exception] {str(e)}"

def render_test_page():
    # --- Session State ---
    if "gptlab_chat_history" not in st.session_state:
        st.session_state.gptlab_chat_history = []
    if "gptlab_typing" not in st.session_state:
        st.session_state.gptlab_typing = False
    if "gptlab_system_prompt" not in st.session_state:
        st.session_state.gptlab_system_prompt = "You are a helpful AI assistant."
    if "gptlab_input" not in st.session_state:
        st.session_state.gptlab_input = ""
    if "gptlab_model" not in st.session_state:
        st.session_state.gptlab_model = MODEL_OPTIONS[0]
    if "gptlab_temp" not in st.session_state:
        st.session_state.gptlab_temp = 0.2
    if "gptlab_max_tokens" not in st.session_state:
        st.session_state.gptlab_max_tokens = 200

    # --- Sidebar Settings ---
    with st.sidebar:
        st.markdown("## ⚙️ Chat Settings")
        st.session_state.gptlab_system_prompt = st.text_area("System Prompt", value=st.session_state.gptlab_system_prompt, key="sys_prompt")
        selected_model = st.selectbox("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(st.session_state.gptlab_model) if st.session_state.gptlab_model in MODEL_OPTIONS else 0, key="chat_model")
        st.session_state.gptlab_model = selected_model
        st.session_state.gptlab_temp = st.slider("Temperature", min_value=0.0, max_value=1.0, value=st.session_state.gptlab_temp, step=0.05, key="chat_temp")
        st.session_state.gptlab_max_tokens = st.number_input("Max Tokens", min_value=1, max_value=2048, value=st.session_state.gptlab_max_tokens, step=1, key="chat_max_tokens")
        st.markdown("---")
        st.markdown("**Powered by Tampere University GPT-Lab**")

    # --- Header ---
    st.markdown("""
    <style>
    .gptlab-header {text-align:center; margin-top:0.7em; margin-bottom:0.2em;}
    .gptlab-logo {font-size:2em;}
    .gptlab-title {font-size:1.7em; font-weight:700; margin-bottom:0.1em;}
    .gptlab-desc {font-size:1em; color:#666; margin-bottom:0.7em;}
    .gptlab-chat-area {max-width:1000px; width:90vw; margin:0 auto; background:#fff; border-radius:1.2em; box-shadow:0 2px 12px rgba(0,0,0,0.04); padding:1em 1.2em 0.5em 1.2em; min-height:500px; display:flex; flex-direction:column; height:65vh; overflow-y:auto;}
    .gptlab-bubble {border-radius:1.2em; padding:0.7em 1.1em; max-width:95%; font-size:1.05rem; margin-bottom:0.1em; word-break:break-word; box-shadow:0 1px 4px rgba(0,0,0,0.03);}
    .gptlab-user {background:#e6f0ff; color:#222; align-self:flex-end; margin-left:10%;}
    .gptlab-assistant {background:#f4f4f8; color:#222; align-self:flex-start; margin-right:10%;}
    .gptlab-meta {font-size:0.8em; color:#888; margin-bottom:0.05em; margin-left:0.5em;}
    .gptlab-divider {height:1px; background:#eee; margin:0.4em 0; border:none;}
    .gptlab-input-row {width:100%; max-width:1000px; margin:0 auto 0.5em auto; display:flex; align-items:center; gap:0.5em; position:fixed; left:0; right:0; bottom:0; background:rgba(255,255,255,0.97); padding:0.7em 0.5em 0.7em 0.5em; z-index:10; border-top:1px solid #eee;}
    .gptlab-input-box {flex:1; border-radius:2em; border:1.2px solid #e0e0e0; padding:0.7em 1.2em; font-size:1.05rem; outline:none; background:#fafbfc; transition:border 0.2s;}
    .gptlab-input-box:focus {border:1.2px solid #a0c4ff; background:#fff;}
    .gptlab-send-btn {border:none; background:#222; color:#fff; border-radius:50%; width:2.3em; height:2.3em; font-size:1.1em; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:background 0.2s;}
    .gptlab-send-btn:hover {background:#0052cc;}
    .gptlab-action-row {max-width:1000px; width:90vw; margin:0 auto 0.2em auto; display:flex; justify-content:flex-end; gap:0.5em;}
    @media (max-width:1100px){.gptlab-chat-area,.gptlab-input-row,.gptlab-action-row{max-width:98vw;}}
    @media (max-width:700px){.gptlab-chat-area,.gptlab-input-row,.gptlab-action-row{max-width:100vw; padding-left:0.2em; padding-right:0.2em;}}
    </style>
    """, unsafe_allow_html=True)
    st.markdown("""
    <div class='gptlab-header'>
        <div class='gptlab-logo'>🧪</div>
        <div class='gptlab-title'>GPT-Lab Chat</div>
        <div class='gptlab-desc'>Chat with your private LLMs hosted at Tampere University GPT-Lab.<br>All messages are processed securely on your own infrastructure.</div>
    </div>
    """, unsafe_allow_html=True)

    # --- Action Row (Clear/Export) ---
    st.markdown("<div class='gptlab-action-row'>", unsafe_allow_html=True)
    colA, colB = st.columns([1,1])
    with colA:
        if st.button("🧹 Clear Chat", help="Clear all messages"):
            st.session_state.gptlab_chat_history = []
            st.experimental_rerun()
    with colB:
        if st.session_state.gptlab_chat_history:
            chat_md = ""
            for msg in st.session_state.gptlab_chat_history:
                who = "**You:**" if msg["role"] == "user" else "**Assistant:**"
                chat_md += f"{who}\n{msg['content']}\n\n"
            st.download_button("⬇️ Export Chat", chat_md, file_name="gptlab_chat.md", help="Download chat as markdown")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Chat Area ---
    st.markdown("<div class='gptlab-chat-area' id='gptlab-chat-area'>", unsafe_allow_html=True)
    if not st.session_state.gptlab_chat_history:
        st.markdown("<div class='chat-empty-prompt'>What can I help with?</div>", unsafe_allow_html=True)
    else:
        for i, msg in enumerate(st.session_state.gptlab_chat_history):
            timestamp = msg.get("time", "")
            if not timestamp:
                timestamp = datetime.now().strftime("%H:%M:%S")
            if msg["role"] == "user":
                st.markdown(f"<div class='gptlab-meta'>🧑 You • {timestamp}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='gptlab-bubble gptlab-user'>{msg['content']}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='gptlab-meta'>🤖 Assistant • {timestamp}</div>", unsafe_allow_html=True)
                st.markdown(f"<div class='gptlab-bubble gptlab-assistant'>", unsafe_allow_html=True)
                st.markdown(msg['content'])
                st.markdown("</div>", unsafe_allow_html=True)
            if i < len(st.session_state.gptlab_chat_history) - 1:
                st.markdown("<hr class='gptlab-divider'>", unsafe_allow_html=True)
        if st.session_state.gptlab_typing:
            st.markdown("<div class='gptlab-meta'>🤖 Assistant is typing...</div>", unsafe_allow_html=True)
            st.markdown("<div class='gptlab-bubble gptlab-assistant'>...<span class='blinking-cursor'>|</span></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Input Row (fixed at bottom) ---
    st.markdown("<div style='height:2.5em'></div>", unsafe_allow_html=True)  # Spacer for fixed input
    st.markdown("<div class='gptlab-input-row'>", unsafe_allow_html=True)
    input_col, btn_col = st.columns([0.92, 0.08])
    with input_col:
        user_input = st.text_input("", value=st.session_state.gptlab_input, key="chat_input", placeholder="Type your message... (Enter to send, Shift+Enter for newline)", label_visibility="collapsed")
    with btn_col:
        send_clicked = st.button("➤", key="send_btn", help="Send message")
    st.markdown("</div>", unsafe_allow_html=True)

    # --- Handle Send ---
    if send_clicked and user_input.strip():
        st.session_state.gptlab_chat_history.append({
            "role": "user",
            "content": user_input.strip(),
            "time": datetime.now().strftime("%H:%M:%S")
        })
        st.session_state.gptlab_typing = True
        st.session_state.gptlab_input = ""
        st.experimental_rerun()
    elif send_clicked:
        st.session_state.gptlab_input = ""

    # --- Assistant Reply ---
    if st.session_state.gptlab_typing:
        with st.spinner("Waiting for LLM response..."):
            last_user_msg = st.session_state.gptlab_chat_history[-1]["content"]
            prompt = (st.session_state.gptlab_system_prompt + "\n" if st.session_state.gptlab_system_prompt else "") + last_user_msg
            reply = gptlab_chat(
                prompt,
                st.session_state.gptlab_model,
                st.session_state.gptlab_temp,
                st.session_state.gptlab_max_tokens
            )
        st.session_state.gptlab_chat_history.append({
            "role": "assistant",
            "content": reply,
            "time": datetime.now().strftime("%H:%M:%S")
        })
        st.session_state.gptlab_typing = False
        st.experimental_rerun()

    # --- Footer ---
    st.markdown("""
    <div style='text-align:center; color:#aaa; font-size:0.95em; margin-top:1em;'>
    GPT-Lab Chat &copy; 2024 &bull; Powered by Tampere University GPT-Lab
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    render_test_page() 