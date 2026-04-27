import streamlit as st
import requests
import time

API_URL = "http://localhost:8001/ask"

st.set_page_config(
    page_title="Agentic News Chatbot",
    page_icon="🧠",
    layout="centered"
)

# -----------------------
# Sidebar
# -----------------------

with st.sidebar:

    st.title("⚙️ Controls")

    if st.button("🔄 Reset Chat"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("---")

    st.info("Agentic News Dataset Chatbot")

# -----------------------
# CSS
# -----------------------

st.markdown("""
<style>

.user-msg {
    background-color: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 12px 0;
    width: fit-content;
    margin-left: auto;
    max-width: 70%;
    white-space: pre-line;
}

.bot-msg {
    background-color: #1f2937;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 12px 0;
    width: fit-content;
    max-width: 70%;
    white-space: pre-line;
}

.typing {
    color: #9ca3af;
    font-style: italic;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# Header
# -----------------------

st.title("🧠 Agentic News Chatbot")
st.write("Ask questions about the dataset.")

# -----------------------
# Session State
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------
# Chat Display
# -----------------------

for msg in st.session_state.messages:

    if msg["role"] == "user":
        st.markdown(
            f'<div class="user-msg">{msg["content"]}</div>',
            unsafe_allow_html=True
        )

    else:
        st.markdown(
            f'<div class="bot-msg">{msg["content"]}</div>',
            unsafe_allow_html=True
        )

# -----------------------
# Chat Input
# -----------------------

prompt = st.chat_input("Ask a question about the dataset...")

if prompt:

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    # Force rerun so message appears immediately
    st.rerun()

# -----------------------
# Generate Bot Response
# -----------------------

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    question = st.session_state.messages[-1]["content"]

    thinking = st.empty()
    thinking.markdown(
        '<div class="bot-msg typing">Bot is thinking...</div>',
        unsafe_allow_html=True
    )

    try:

        response = requests.post(
            API_URL,
            json={"question": question}
        )

        result = response.json()

        answer = result.get("answer", "No response received.")

    except Exception as e:

        answer = f"Error contacting API: {e}"

    time.sleep(0.4)

    thinking.empty()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.rerun()