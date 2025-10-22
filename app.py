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

st.markdown(f"""
<style>
  @keyframes sunsetMove{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
  @keyframes breathe {{
    0% {{transform: scale(1); opacity: 0.8;}}
    50% {{transform: scale(1.5); opacity: 1;}}
    100% {{transform: scale(1); opacity: 0.8;}}
  }}
  html,body,[data-testid="stAppViewContainer"],[data-testid="stSidebar"],[data-testid="stMainBlockContainer"]{{
    background:linear-gradient(135deg,#2a0e2f,#6a225f,#a34aa0,#f6b07a,#ffdca8);
    background-size:400% 400%;
    animation:sunsetMove 30s ease infinite;
    color:#f7f7f7;
    {"font-family:NomiCustom,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;" if font_b64 else "font-family:-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"}
  }}
  {"@font-face {font-family:'NomiCustom';src:url(data:font/woff2;base64,"+font_b64+") format('woff2');font-weight:100 900;font-style:normal;font-display:swap;}" if font_b64 else ""}

  [data-testid="stAppViewContainer"] > .main, [data-testid="stMainBlockContainer"], section.main, .block-container {{
    background: transparent !important; box-shadow: none !important; border: none !important; padding: 0 !important;
  }}
  [data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
    background: rgba(0,0,0,0.15) !important; backdrop-filter: blur(8px); border: none !important; box-shadow: none !important;
  }}
  [data-testid="stBottom"], [data-testid="stChatInputContainer"], [data-testid="stChatInput"] {{
    background: transparent !important; border: none !important; box-shadow: none !important;
  }}
  textarea {{
    background: rgba(255,255,255,0.1) !important; color: #fff !important; border: none !important; border-radius: 12px !important; padding: 10px !important;
  }}
  .app-title{{text-align:center;font-weight:900;font-size:clamp(56px,8vw,110px);margin:0 0 16px 0;letter-spacing:.5px;}}
  .app-title .therep{{font-weight:400;text-transform:lowercase}}
  .chat-wrap{{display:flex;flex-direction:column;gap:12px}}
  .bubble{{display:inline-block;padding:12px 16px;line-height:1.5;max-width:78%;white-space:pre-wrap;word-wrap:break-word;border:none!important;border-radius:18px;}}
  .user-bub.right{{align-self:flex-end;background:transparent!important;font-weight:600;color:#fff;text-shadow:0 0 4px rgba(0,0,0,0.25);}}
  .ai-bub.left{{align-self:flex-start;background:rgba(255,255,255,0.08)!important;-webkit-backdrop-filter:blur(8px);backdrop-filter:blur(8px);}}
  .breathing-circle {{
    width:120px;height:120px;margin:25px auto;background:rgba(255,255,255,0.25);
    border-radius:50%;animation:breathe 8s ease-in-out infinite;
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
1. **Start by gently exploring** what’s happening before suggesting a skill. Ask 1–2 clarifying questions (e.g., “Can you tell me what’s been making you feel anxious lately?”).
2. **Choose one single CBT or DBT skill** that fits their emotion — only after understanding their situation.
   - Panic → grounding or paced breathing
   - Anger → opposite action or mindfulness
   - Sadness → behavioral activation or self-soothing
   - Overwhelm → STOP skill or wise mind
   - Guilt/Shame → self-compassion or reframing
3. **Deliver the skill in small, paced steps.**
   - If the step involves breathing, mention “Take a deep breath in for 4 seconds...” etc.
   - If multiple steps, present one → pause for user → next.
4. **Use Markdown** for formatting (bold, italics, lists).
5. End with a calm reassurance (“You’re doing really well just by pausing to breathe.”)
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

            steps = reply.split("\n\n")
            for step in steps:
                if "breathe" in step.lower():
                    st.markdown('<div class="breathing-circle"></div>', unsafe_allow_html=True)
                placeholder.markdown(step, unsafe_allow_html=False)
                if st.button("Continue", key=str(uuid.uuid4())):
                    continue
                time.sleep(3)

            chat["messages"].append({"role": "assistant", "content": reply})
        except Exception as e:
            error_text = f"Error: {e}"
            placeholder.markdown(error_text, unsafe_allow_html=False)
            chat["messages"].append({"role": "assistant", "content": error_text})
