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

# -------------------- Firebase --------------------
def load_firebase_config():
    env_cfg = {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID"),
        "databaseURL": os.getenv("FIREBASE_DATABASE_URL", "")
    }
    if all(env_cfg.get(k) for k in ["apiKey","authDomain","projectId","storageBucket","messagingSenderId","appId"]):
        return env_cfg
    if os.path.exists("firebase_config.json"):
        with open("firebase_config.json") as f: return json.load(f)
    st.error("Firebase config not found."); st.stop()

firebaseConfig = load_firebase_config()
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "user" not in st.session_state: st.session_state.user = None

# -------------------- Font --------------------
FONT_PATH = "fonts/Quicksand-VariableFont_wght.woff2"
font_b64 = ""
if os.path.exists(FONT_PATH):
    with open(FONT_PATH,"rb") as f: font_b64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------- STYLE --------------------
st.markdown(f"""
<style>
@keyframes sunsetSlow {{
  0% {{ background-position: 0% 50%; }}
  25% {{ background-position: 50% 100%; }}
  50% {{ background-position: 100% 50%; }}
  75% {{ background-position: 50% 0%; }}
  100% {{ background-position: 0% 50%; }}
}}
[data-testid="stAppViewContainer"] {{
  background: linear-gradient(-45deg, #f6b07a, #ffbf90, #ffdca8, #ffe7be);
  background-size: 600% 600%;
  animation: sunsetSlow 90s ease-in-out infinite;
  color: #fff !important;
}}
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
  background: linear-gradient(-45deg, #f6b07a, #ffdca8)!important;
  backdrop-filter: blur(12px);
  color:#fff!important;
  border:none!important;
}}
[data-testid="stHeader"], [data-testid="stToolbar"], footer, [data-testid="stDecoration"] {{ display:none!important; }}
.block-container {{ background:transparent!important; color:#fff!important; }}
.app-title {{
  text-align:center; font-weight:900;
  font-size:clamp(56px,8vw,110px); margin:0 0 16px 0;
  color:#fff; letter-spacing:0.5px;
}}
.app-title .therep {{ font-weight:300; text-transform:lowercase; }}

/* ---------- Login layout ---------- */
.login-shell{{display:flex;gap:0;height:100vh;align-items:stretch;margin-top:-2rem}}
.brand-side{{
  flex:1; display:flex; flex-direction:column; justify-content:center; padding:6vw;
  color:#fff;
}}
.brand-title{{font-weight:800;font-size:clamp(44px,6.5vw,84px);line-height:1.05;margin:0}}
.brand-title .thin{{font-weight:300;}}
.brand-sub{{margin-top:.5rem;font-size:1.15rem;opacity:.9}}
.form-side{{flex:1;display:flex;align-items:center;justify-content:center;}}
.form-card{{
  width:min(92%,420px);background:#fff;color:#222;border-radius:20px;
  box-shadow:0 18px 50px rgba(0,0,0,.18);padding:40px 34px;
}}
.form-card h2{{margin:0 0 14px 0;font-weight:800;font-size:1.6rem}}
.stTextInput>div>div>input{{
  border-radius:12px!important;border:1px solid #ddd!important;color:#222!important;
  padding:10px 14px!important;
}}
.primary-btn{{
  width:100%;border:none;border-radius:999px;padding:12px 0;font-weight:700;
  background:linear-gradient(90deg,#f6b07a,#ffdca8);
  color:#442a1a;cursor:pointer;transition:.2s ease;
}}
.primary-btn:hover{{filter:brightness(1.05)}}
.form-note{{text-align:center;margin-top:12px;color:#666}}
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

# -------------------- Login Page --------------------
def login_page():
    st.markdown('<div class="login-shell">', unsafe_allow_html=True)
    st.markdown("""
    <div class="brand-side">
      <div class="brand-title"><span class="thin">therep</span>Ai</div>
      <div class="brand-sub">inhale, exhale.</div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div class="form-side"><div class="form-card">', unsafe_allow_html=True)
    st.markdown('<h2>Sign in</h2>', unsafe_allow_html=True)

    choice = st.radio("", ["Sign In", "Sign Up", "Continue as Guest"], horizontal=True, label_visibility="collapsed")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Sign Up":
        if st.button("Create Account", key="signup_btn", use_container_width=True):
            try:
                auth.create_user_with_email_and_password(email, password)
                st.success("Account created successfully! You can sign in now.")
            except Exception as e:
                st.error(f"Error: {e}")

    elif choice == "Sign In":
        if st.button("Sign In", key="signin_btn", use_container_width=True):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.user = user
                st.session_state.logged_in = True
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

    elif choice == "Continue as Guest":
        if st.button("Enter Guest Mode", key="guest_btn", use_container_width=True):
            st.session_state.logged_in = True
            st.session_state.user = {"email": "guest@therepai.app"}
            st.success("You’re in guest mode! Conversations won’t be saved.")
            st.rerun()

    st.markdown("""
      <div class="form-note">
        New here? Choose "Sign Up" or explore as Guest.
      </div>
    </div></div></div>
    """, unsafe_allow_html=True)

# -------------------- Main App --------------------
if not st.session_state.logged_in:
    login_page()
    st.stop()

# -------------------- Chat memory --------------------
if "chats" not in st.session_state: st.session_state.chats = {}
if "current_chat_id" not in st.session_state:
    cid = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = cid
    st.session_state.chats[cid] = {"title": "New chat", "messages": []}

def get_chat(): return st.session_state.chats[st.session_state.current_chat_id]
def new_chat():
    cid = str(uuid.uuid4())[:8]
    st.session_state.current_chat_id = cid
    st.session_state.chats[cid] = {"title": "New chat", "messages": []}

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("### therepAi")
    st.caption("Your conversations (private to this session).")
    if st.button("➕ New chat", use_container_width=True): new_chat()
    chats = list(st.session_state.chats.keys())
    sel = st.selectbox("Open chat", chats, index=chats.index(st.session_state.current_chat_id),
                       format_func=lambda x: st.session_state.chats[x]["title"])
    st.session_state.current_chat_id = sel
    if st.button("Log out", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

# -------------------- Header --------------------
st.markdown('<div class="app-title"><span class="therep">therep</span>Ai</div>', unsafe_allow_html=True)

# -------------------- Chat display --------------------
chat = get_chat()
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in chat["messages"]:
    role, msg = m["role"], m["content"]
    cls = "user-bub right" if role == "user" else "ai-bub left"
    st.markdown(f'<div class="bubble {cls}">{msg}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Input --------------------
user_text = st.chat_input("Tell me what’s on your mind...")
if user_text:
    chat["messages"].append({"role": "user", "content": user_text})
    st.markdown(f'<div class="bubble user-bub right">{user_text}</div>', unsafe_allow_html=True)
    crisis = ["kill myself", "suicide", "hurt myself", "die"]
    if any(w in user_text.lower() for w in crisis):
        reply = "**It sounds like you might be in danger.** Please reach out right now — call or text **988** (U.S.). 💛"
    else:
        context = "\n".join(f"{m['role']}: {m['content']}" for m in chat["messages"][-8:])
        prompt = f"""
You are Pai — a gentle CBT & DBT-based guide (not a therapist).
Start with 1–2 clarifying questions, introduce one appropriate skill, and guide the user calmly.
Use **bold** steps and *empathetic* tone.
End with a short grounding reflection.
Recent chat:
{context}
User: {user_text}
Respond as Pai now.
"""
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user","content":prompt}],
                temperature=0.55, max_tokens=400)
            reply = resp.choices[0].message.content.strip()
        except Exception as e:
            reply = f"Error: {e}"
    placeholder = st.empty(); typed=""
    for c in reply:
        typed += c
        placeholder.markdown(f'<div class="bubble ai-bub left">{typed}</div>', unsafe_allow_html=True)
        time.sleep(0.02)
    chat["messages"].append({"role": "assistant","content":reply})
