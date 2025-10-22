# app.py
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
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
st.set_page_config(page_title="therepAi", page_icon="🧠", layout="centered")

# --- session state bootstrap ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Paths
CONV_DIR = "conversations"
INDEX_PATH = os.path.join(CONV_DIR, "index.json")
FONT_PATH = "fonts/Quicksand-VariableFont_wght.woff2"
os.makedirs(CONV_DIR, exist_ok=True)

# -------------------- Font (embed base64, optional) --------------------
font_b64 = ""
if os.path.exists(FONT_PATH):
    with open(FONT_PATH, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")

# -------------------- Styles --------------------
st.markdown(f"""
<style>
  @keyframes sunsetMove{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
  html,body,[data-testid="stAppViewContainer"],[data-testid="stSidebar"],[data-testid="stMainBlockContainer"]{{
    background:linear-gradient(135deg,#2a0e2f,#6a225f,#a34aa0,#f6b07a,#ffdca8);
    background-size:400% 400%;
    animation:sunsetMove 30s ease infinite;
    color:#f7f7f7;
    {"font-family:NomiCustom, -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, Helvetica, Arial, sans-serif;" if font_b64 else "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"}
  }}

  {"@font-face {font-family:'NomiCustom';src:url(data:font/woff2;base64,"+font_b64+") format('woff2');font-weight:100 900;font-style:normal;font-display:swap;}" if font_b64 else ""}

  /* remove all boxes, cards, and padding */
  [data-testid="stSidebar"],[data-testid="stSidebar"]>div,[aria-label="Main menu"]+div,
  [data-testid="stAppViewContainer"]>.main,.block-container,
  [data-testid="stHeader"],header,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{{
    border:none!important;box-shadow:none!important;background:transparent!important;
  }}

  /* kill bottom bar completely */
  [data-testid="stBottom"],[data-testid="stBottomBlock"],[data-testid="stChatInput"],[data-testid="stChatInputContainer"]{{
    background:transparent!important;
    border:none!important;
    box-shadow:none!important;
  }}
  [data-testid="stChatInput"] *{{
    background:transparent!important;
    border:none!important;
    box-shadow:none!important;
  }}

  /* send button minimal */
  [data-testid="stBaseButton-secondaryFormSubmit"]{{
    background:rgba(255,255,255,0.18)!important;
    color:#fff!important;
    border:none!important;
  }}

  /* title */
  .app-title{{
    text-align:center;
    font-weight:900;
    font-size:clamp(56px,8vw,110px);
    margin:0 0 16px 0;
    letter-spacing:.5px;
  }}
  .app-title .therep{{text-transform:lowercase}}

  /* chat layout + bubbles */
  .chat-wrap{{display:flex;flex-direction:column;gap:12px}}
  .bubble{{
    display:inline-block;padding:12px 16px;line-height:1.5;max-width:78%;
    white-space:pre-wrap;word-wrap:break-word;border:none!important;border-radius:18px;
  }}
  .user-bub.right{{
    align-self:flex-end;background:transparent!important;font-weight:600;
    color:#fff;text-shadow:0 0 4px rgba(0,0,0,0.25);
  }}
  .ai-bub.left{{
    align-self:flex-start;background:rgba(255,255,255,0.08)!important;
    -webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);
  }}

  /* FINAL OVERRIDE: remove black background under chat input */
  section.main div[data-testid="stBottom"],
  section.main div[data-testid="stChatInput"],
  section.main div[data-testid="stBottomBlock"],
  section.main div[data-testid="stChatInputContainer"] {{
    background-color: transparent !important;
    background: transparent !important;
    box-shadow: none !important;
    border: none !important;
  }}
  section.main div[data-testid="stChatInputContainer"] textarea {{
    background: transparent !important;
    color: #fff !important;
  }}

  [data-testid="stMainBlockContainer"]>div:first-child{{max-width:900px;margin:0 auto}}
</style>
""", unsafe_allow_html=True)

# -------------------- File-backed chat helpers --------------------
def load_index():
    if not os.path.exists(INDEX_PATH):
        return []
    try:
        with open(INDEX_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_index(index):
    with open(INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2)

def chat_path(chat_id):
    return os.path.join(CONV_DIR, f"{chat_id}.json")

def load_chat(chat_id):
    path = chat_path(chat_id)
    if not os.path.exists(path):
        return {"id": chat_id, "title": "New chat", "created_at": datetime.utcnow().isoformat(), "messages": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_chat(chat):
    with open(chat_path(chat["id"]), "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2)

def create_new_chat():
    chat_id = uuid.uuid4().hex[:10]
    title = "New chat"
    chat = {"id": chat_id, "title": title, "created_at": datetime.utcnow().isoformat(), "messages": []}
    save_chat(chat)
    idx = load_index()
    idx.insert(0, {"id": chat_id, "title": title})
    save_index(idx)
    st.session_state.current_chat_id = chat_id

def ensure_current_chat():
    if "current_chat_id" not in st.session_state:
        idx = load_index()
        if idx:
            st.session_state.current_chat_id = idx[0]["id"]
        else:
            create_new_chat()

def rename_current_chat(new_title):
    idx = load_index()
    for row in idx:
        if row["id"] == st.session_state.current_chat_id:
            row["title"] = new_title or row["title"]
    save_index(idx)
    chat = load_chat(st.session_state.current_chat_id)
    chat["title"] = new_title or chat["title"]
    save_chat(chat)

def delete_current_chat():
    cid = st.session_state.current_chat_id
    try:
        os.remove(chat_path(cid))
    except FileNotFoundError:
        pass
    idx = [row for row in load_index() if row["id"] != cid]
    save_index(idx)
    if idx:
        st.session_state.current_chat_id = idx[0]["id"]
    else:
        create_new_chat()

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("### therepAi")
    st.caption("Your conversations (saved locally).")
    if st.button("➕ New chat", use_container_width=True):
        create_new_chat()

    index = load_index()
    ensure_current_chat()

    id_to_title = {row["id"]: row["title"] for row in index}
    current_id = st.session_state.current_chat_id
    options = [row["id"] for row in index] or [current_id]
    selection = st.selectbox(
        "Open chat",
        options,
        index=options.index(current_id) if current_id in options else 0,
        format_func=lambda cid: id_to_title.get(cid, "New chat"),
    )
    st.session_state.current_chat_id = selection

    with st.expander("Chat settings"):
        new_title = st.text_input("Rename", value=id_to_title.get(selection, "New chat"))
        col_r, col_d = st.columns(2)
        if col_r.button("Save name", use_container_width=True):
            rename_current_chat(new_title.strip())
        if col_d.button("Delete chat", use_container_width=True):
            delete_current_chat()
            st.rerun()

# -------------------- Header --------------------
st.markdown('<div class="app-title"><span class="therep">therep</span>Ai</div>', unsafe_allow_html=True)

# -------------------- Load Chat --------------------
ensure_current_chat()
chat = load_chat(st.session_state.current_chat_id)
st.session_state.messages = chat["messages"]

# -------------------- Display Chat --------------------
st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
for m in chat["messages"]:
    role = m.get("role", "assistant")
    txt = m.get("content", "")
    side = "right" if role == "user" else "left"
    bub = "user-bub" if role == "user" else "ai-bub"
    st.markdown(f'<div class="bubble {bub} {side}">{txt}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------- Input --------------------
user_text = st.chat_input("Tell me what’s on your mind...")

if user_text:
    chat["messages"].append({"role": "user", "content": user_text})
    st.markdown(f'<div class="bubble user-bub right">{user_text}</div>', unsafe_allow_html=True)

    if chat["title"] == "New chat":
        rename_current_chat(user_text.strip()[:40])

    crisis_words = ["kill myself", "suicide", "hurt myself", "die"]
    if any(w in user_text.lower() for w in crisis_words):
        reply = (
            "It sounds like you might be in danger. Please reach out right now. "
            "Call or text 988 in the U.S., or your local helpline. You are not alone. 💛"
        )
        st.markdown(f'<div class="bubble ai-bub left">{reply}</div>', unsafe_allow_html=True)
        chat["messages"].append({"role": "assistant", "content": reply})
        save_chat(chat)
    else:
        # ----- build short context for the reply (last 8 msgs) -----
        memory_context = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}" for m in chat["messages"][-8:]
        )

        prompt = f"""
You are pai, the warm, emotionally intelligent AI companion in an app called therepAi.
Speak like a grounded, kind, self-aware friend. Avoid diagnosis; keep it practical and gentle.
Offer one validating line and one tiny micro-step (CBT/DBT/mindfulness inspired).

Recent chat:
{memory_context}

Reply to the user's latest message with warmth and one gentle next step.
""".strip()

        # assistant reply with typing effect (left, glass)
        placeholder = st.empty()
        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=350,
            )
            reply = (resp.choices[0].message.content or "").strip()

            # trim any "Pai:" prefix
            for p in ["Pai:", "PAI:", "pai:", "Pai -", "pai -"]:
                if reply.startswith(p):
                    reply = reply[len(p):].lstrip()
                    break

            typed = ""
            for w in reply.split():
                typed += w + " "
                placeholder.markdown(f'<div class="bubble ai-bub left">{typed}▌</div>', unsafe_allow_html=True)
                time.sleep(0.06)
            placeholder.markdown(f'<div class="bubble ai-bub left">{typed}</div>', unsafe_allow_html=True)

            chat["messages"].append({"role": "assistant", "content": reply})
            save_chat(chat)
        except Exception as e:
            placeholder.markdown(f'<div class="bubble ai-bub left">Error: {e}</div>', unsafe_allow_html=True)
            save_chat(chat)
S