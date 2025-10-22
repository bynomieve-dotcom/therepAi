import os
import time
import json
import uuid
import base64
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

# -------------------- Setup --------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key not found. Please set it in Render Environment Variables.")
    st.stop()

client = OpenAI(api_key=api_key)
st.set_page_config(page_title="therepAi", page_icon="🧠", layout="centered")

# -------------------- Font + Style --------------------
FONT_PATH = "fonts/Quicksand-VariableFont_wght.woff2"
font_b64 = ""
if os.path.exists(FONT_PATH):
    with open(FONT_PATH, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")

# --- STYLE ---
st.markdown(f"""
<style>
  :root {{
    --primary-bg: linear-gradient(135deg, #2a0e2f, #6a225f, #a34aa0, #f6b07a, #ffdca8);
  }}

  @keyframes sunsetMove {{
    0% {{background-position:0% 50%;}}
    50% {{background-position:100% 50%;}}
    100% {{background-position:0% 50%;}}
  }}
  @keyframes breathe {{
    0% {{transform: scale(1); opacity: 0.8;}}
    50% {{transform: scale(1.5); opacity: 1;}}
    100% {{transform: scale(1); opacity: 0.8;}}
  }}

  html, body {{
    background: var(--primary-bg);
    background-size: 400% 400%;
    animation: sunsetMove 30s ease infinite;
    height: 100%;
    margin: 0;
    overflow: hidden;
    color: #fff !important;
  }}

  [data-testid="stAppViewContainer"],
  [data-testid="stMainBlockContainer"],
  .block-container,
  section.main {{
    background: transparent !important;
    color: #fff !important;
  }}

  [data-testid="stHeader"], footer, [data-testid="stToolbar"], [data-testid="stDecoration"] {{
    display: none !important;
  }}

  [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
    background: rgba(40, 0, 60, 0.65) !important;
    backdrop-filter: blur(12px);
    border: none !important;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.25);
    color: #fff !important;
  }}

  .app-title {{
    text-align: center;
    font-weight: 900;
    font-size: clamp(56px, 8vw, 110px);
    margin: 0 0 16px 0;
    letter-spacing: .5px;
    color: #fff;
  }}
  .app-title .therep {{
    font-weight: 400;
    text-transform: lowercase;
  }}

  .chat-wrap {{display:flex;flex-direction:column;gap:12px;}}
  .bubble {{
    display:inline-block;
    padding:12px 16px;
    line-height:1.5;
    max-width:78%;
    white-space:pre-wrap;
    word-wrap:break-word;
    border:none!important;
    border-radius:18px;
  }}
  .user-bub.right {{
    align-self:flex-end;
    background:transparent!important;
    font-weight:600;
    color:#fff;
    text-shadow:0 0 4px rgba(0,0,0,0.25);
  }}
  .ai-bub.left {{
    align-self:flex-start;
    background:rgba(255,255,255,0.08)!important;
    -webkit-backdrop-filter:blur(8px);
    backdrop-filter:blur(8px);
    color:#fff !important;
  }}

  .breathing-circle {{
    width:120px;
    height:120px;
    margin:25px auto;
    background:rgba(255,255,255,0.25);
    border-radius:50%;
    animation:breathe 8s ease-in-out infinite;
  }}

  [data-testid="stChatInputContainer"] textarea {{
    background: rgba(255,255,255,0.15) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 20px !important;
    padding: 10px !important;
  }}
  [data-testid="stBottom"], [data-testid="stChatInputContainer"], [data-testid="stChatInput"] {{
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
  }}
</style>
""", unsafe_allow_html=True)

# -------------------- Private per-session chat storage --------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = chat_id
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": [], "created_at": datetime.utcnow().isoformat()}

def create_new_chat():
    chat_id = str(uuid.uuid4())[:8]
    st.session_state.chats[chat_id] = {"title": "New chat", "messages": [], "created_at": datetime.utcnow().isoformat()}
    st.session_state.current_chat_id = chat_id

def rename_current_chat(new_title):
    st.session_state.chats[st.session_state.current_chat_id]["title"] = new_title or "Untitled"

def delete_current_chat():
    del st.session_state.chats[st.session_state.current_chat_id]
    if st.session_state.chats:
        st.session_state.current_chat_id = next(iter(st.session_state.chats))
    else:
        create_new_chat()

def get_current_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("### therepAi")
    st.caption("Your conversations (private to this session).")

    if st.button("➕ New chat", use_container_width=True):
        create_new_chat()

    chat_options = list(st.session_state.chats.keys())
    current_id = st.session_state.current_chat_id
    selection = st.selectbox(
        "Open chat",
        chat_options,
        index=chat_options.index(current_id),
        format_func=lambda cid: st.session_state.chats[cid]["title"],
    )
    st.session_state.current_chat_id = selection

    with st.expander("Chat settings"):
        new_title = st.text_input("Rename", value=get_current_chat()["title"])
        col_r, col_d = st.columns(2)
        if col_r.button("Save name", use_container_width=True):
            rename_current_chat(new_title.strip())
        if col_d.button("Delete chat", use_container_width=True):
            delete_current_chat()
            st.rerun()

# -------------------- Header --------------------
st.markdown('<div class="app-title"><span class="therep">therep</span>Ai</div>', unsafe_allow_html=True)

# -------------------- Display chat --------------------
chat = get_current_chat()
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in chat["messages"]:
    if m["role"] == "user":
        st.markdown(f'<div class="bubble user-bub right">{m["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(m["content"], unsafe_allow_html=False)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Input + Response --------------------
user_text = st.chat_input("Tell me what’s on your mind...")

if user_text:
    chat["messages"].append({"role": "user", "content": user_text})
    st.markdown(f'<div class="bubble user-bub right">{user_text}</div>', unsafe_allow_html=True)

    crisis_words = ["kill myself", "suicide", "hurt myself", "die"]
    if any(w in user_text.lower() for w in crisis_words):
        reply = (
            "**It sounds like you might be in danger.** Please reach out right now — "
            "you can call or text **988** in the U.S., or your local helpline. "
            "You are *not* alone, and your safety matters deeply. 💛"
        )
        st.markdown(reply, unsafe_allow_html=False)
        chat["messages"].append({"role": "assistant", "content": reply})
    else:
        memory_context = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in chat["messages"][-10:]
        )

        prompt = f"""
You are Pai — a warm, supportive CBT & DBT-based guide.
You are *not* a therapist — your purpose is to help users apply one appropriate skill for their emotional state, guiding them slowly and calmly.

When responding:
1. Begin by gently asking 1–2 clarifying questions about what’s going on, rather than jumping to a skill immediately.
2. Then choose **one single skill** that fits their emotion (e.g., grounding for panic, self-compassion for guilt).
3. Deliver that skill naturally, with pauses and short sentences.
4. If the response involves breathing, describe it slowly and gently — Pai should walk the user through a short round.
5. Use Markdown for readability: **bold** steps, *italics* for empathy, bullet points for exercises.
6. End with one grounding reassurance like “You’re doing really well just by pausing to breathe.”

If asked your name, say: “My name is Pai.”

Recent chat:
{memory_context}

Now respond to the user's latest message as Pai, following these rules exactly.
""".strip()

        placeholder = st.empty()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.55,
                max_tokens=400,
            )
            reply = (resp.choices[0].message.content or "").strip()

            if any(word in reply.lower() for word in ["breathe", "breathing", "inhale", "exhale"]):
                st.markdown('<div class="breathing-circle"></div>', unsafe_allow_html=True)
                time.sleep(1)

            typed = ""
            for sentence in reply.split(". "):
                typed += sentence + ". "
                placeholder.markdown(typed, unsafe_allow_html=False)
                time.sleep(0.6)

            chat["messages"].append({"role": "assistant", "content": reply})
        except Exception as e:
            error_text = f"Error: {e}"
            placeholder.markdown(error_text, unsafe_allow_html=False)
            chat["messages"].append({"role": "assistant", "content": error_text})
