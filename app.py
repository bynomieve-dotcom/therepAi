import os, time, json, uuid, base64
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import pyrebase

# -------------------- Setup --------------------
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("OPENAI_API_KEY")
if not api_key:
    st.error("OpenAI API key missing.")
    st.stop()

client = OpenAI(api_key=api_key)
st.set_page_config(page_title="therepAi", page_icon="🧠", layout="centered")

# -------------------- Firebase Setup --------------------
with open("firebase_config.json") as f:
    firebaseConfig = json.load(f)

firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# -------------------- Login Page --------------------
def login_page():
    st.title("therepAi Login")
    st.write("Welcome back to your AI companion")

    choice = st.radio("Select an option:", ["Login", "Sign Up"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Sign Up":
        if st.button("Create Account"):
            try:
                auth.create_user_with_email_and_password(email, password)
                st.success("Account created successfully! You can now log in.")
            except Exception as e:
                st.error(f"Error: {e}")

    elif choice == "Login":
        if st.button("Login"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.session_state.logged_in = True
                st.success("Logged in successfully!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Error: {e}")

# -------------------- Font --------------------
FONT_PATH = "fonts/Quicksand-VariableFont_wght.woff2"
font_b64 = ""
if os.path.exists(FONT_PATH):
    with open(FONT_PATH, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------- STYLE --------------------
st.markdown(f"""
<style>
@keyframes sunsetWave {{
  0%   {{ background-position: 0% 50%; }}
  25%  {{ background-position: 50% 100%; }}
  50%  {{ background-position: 100% 50%; }}
  75%  {{ background-position: 50% 0%; }}
  100% {{ background-position: 0% 50%; }}
}}
[data-testid="stAppViewContainer"] {{
  background: linear-gradient(-45deg, #2a0e2f, #6a225f, #a34aa0, #f6b07a, #ffdca8);
  background-size: 600% 600%;
  animation: sunsetWave 45s ease-in-out infinite;
  color: #fff !important;
}}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
  background: rgba(40,0,60,0.75)!important;
  backdrop-filter: blur(12px);
  color:#fff!important;
  border:none!important;
}}
[data-testid="stHeader"], [data-testid="stToolbar"], footer, [data-testid="stDecoration"] {{
  display:none!important;
}}
.block-container {{
  background:transparent!important;
  color:#fff!important;
}}
.app-title {{
  text-align:center;
  font-weight:900;
  font-size:clamp(56px,8vw,110px);
  margin:0 0 16px 0;
  color:#fff;
  letter-spacing:0.5px;
}}
.app-title .therep {{
  font-weight:400;
  text-transform:lowercase;
}}
.chat-wrap{{display:flex;flex-direction:column;gap:12px;}}
.bubble{{display:inline-block;padding:12px 16px;line-height:1.5;max-width:78%;
white-space:pre-wrap;word-wrap:break-word;border:none!important;border-radius:18px;}}
.user-bub.right{{align-self:flex-end;background:transparent!important;font-weight:600;
color:#fff;text-shadow:0 0 4px rgba(0,0,0,0.25);}}
.ai-bub.left{{align-self:flex-start;background:rgba(255,255,255,0.08)!important;
backdrop-filter:blur(8px);color:#fff!important;}}
[data-testid="stChatInputContainer"] textarea{{background:rgba(255,255,255,0.15)!important;
color:#fff!important;border:none!important;border-radius:20px!important;padding:10px!important;}}
</style>
""", unsafe_allow_html=True)

# -------------------- Main App --------------------
if not st.session_state.logged_in:
    login_page()
    st.stop()  # stop here until user logs in

# -------------------- Chat memory --------------------
if "chats" not in st.session_state:
    st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    cid = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = cid
    st.session_state.chats[cid] = {"title": "New chat", "messages": []}

def get_chat():
    return st.session_state.chats[st.session_state.current_chat_id]

def new_chat():
    cid = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = cid
    st.session_state.chats[cid] = {"title": "New chat", "messages": []}

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("### therepAi")
    st.caption("Your conversations (private to this session).")
    if st.button("➕ New chat", use_container_width=True):
        new_chat()
    chats = list(st.session_state.chats.keys())
    sel = st.selectbox(
        "Open chat",
        chats,
        index=chats.index(st.session_state.current_chat_id),
        format_func=lambda x: st.session_state.chats[x]["title"]
    )
    st.session_state.current_chat_id = sel
    if st.button("Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.experimental_rerun()

# -------------------- Header --------------------
st.markdown('<div class="app-title"><span class="therep">therep</span>Ai</div>', unsafe_allow_html=True)

# -------------------- Chat display --------------------
chat = get_chat()
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in chat["messages"]:
    role = m["role"]
    msg = m["content"]
    if role == "user":
        st.markdown(f'<div class="bubble user-bub right">{msg}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bubble ai-bub left">{msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Input --------------------
user_text = st.chat_input("Tell me what’s on your mind...")

if user_text:
    chat["messages"].append({"role": "user", "content": user_text})
    st.markdown(f'<div class="bubble user-bub right">{user_text}</div>', unsafe_allow_html=True)

    crisis = ["kill myself", "suicide", "hurt myself", "die"]
    if any(w in user_text.lower() for w in crisis):
        reply = "**It sounds like you might be in danger.** Please reach out right now — call or text **988** (U.S.). 💛"
        st.markdown(f'<div class="bubble ai-bub left">{reply}</div>', unsafe_allow_html=True)
        chat["messages"].append({"role": "assistant", "content": reply})
    else:
        context = "\n".join(f"{m['role']}: {m['content']}" for m in chat["messages"][-8:])
        prompt = f"""
You are Pai — a gentle CBT & DBT-based guide (not a therapist).
Start by asking 1–2 clarifying questions about what’s going on.
Then introduce one appropriate skill and walk the user through it calmly, step by step.
Use a soft, caring tone with **bold** steps and *italic* empathy.
End with a short grounding reflection.
Recent chat:
{context}
User: {user_text}
Respond as Pai now.
"""
        placeholder = st.empty()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.55,
                max_tokens=400,
            )
            reply = resp.choices[0].message.content.strip()
            typed = ""
            for char in reply:
                typed += char
                placeholder.markdown(f'<div class="bubble ai-bub left">{typed}</div>', unsafe_allow_html=True)
                time.sleep(0.02)
            chat["messages"].append({"role": "assistant", "content": reply})
        except Exception as e:
            placeholder.markdown(f'<div class="bubble ai-bub left">Error: {e}</div>', unsafe_allow_html=True)
