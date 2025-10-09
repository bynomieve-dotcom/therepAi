import os
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(page_title="College AI Skills Coach", page_icon="🎓", layout="centered")
with st.sidebar:
    st.header("Style")
    theme = st.selectbox("Accent", ["Blue", "Purple", "Green", "Pink"])
    font_size = st.slider("Font size", 14, 22, 16)

accent_map = {"Blue":"#3b82f6","Purple":"#a78bfa","Green":"#22c55e","Pink":"#ec4899"}
st.markdown(f"""
<style>
:root {{ --accent: {accent_map[theme]}; }}
h1, h2, h3 {{ color: var(--accent); }}
.stChatMessage {{ font-size: {font_size}px; }}
div[data-testid="stChatMessageIcon"] svg {{ color: var(--accent); }}
</style>
""", unsafe_allow_html=True)

st.title("College AI Skills Coach")
st.caption("Educational use only — not therapy or medical care. In a crisis call or text 988 (U.S.).")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hey! I'm your skills coach. What’s going on today?"}
    ]

user_text = st.chat_input("Type how you're feeling and press Enter")

if user_text:
    st.chat_message("user").markdown(user_text)

    if any(word in user_text.lower() for word in ["kill myself", "suicide", "die", "hurt myself"]):
        st.chat_message("assistant").error(
            "You might be in danger. Please reach out now: call or text 988 in the U.S. or your local emergency services."
        )
    else:
        prompt = f"""
You are a supportive AI skills coach for college students.
Never diagnose or provide therapy. Offer short, step-by-step CBT/DBT skills (Wise Mind, Opposite Action, Grounding, STOP).
Keep it practical and kind. Guide the user through one 1–5 minute exercise.

User message:
{user_text}
"""
        try:
            with st.spinner("Thinking..."):
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",  # if this errors, try "gpt-4o"
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.5,
                )
            reply = resp.choices[0].message.content
            st.chat_message("assistant").markdown(reply)
        except Exception as e:
            st.chat_message("assistant").error(f"API error: {e}")
