import streamlit as st
import requests
import time

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(
    page_title="Agentic News Chatbot",
    page_icon="🧠",
    layout="centered"
)

# -----------------------
# Custom CSS
# -----------------------

st.markdown("""
<style>

.chat-container {
    max-width: 800px;
    margin: auto;
}

.user-msg {
    background-color: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 10px 0;
    width: fit-content;
    margin-left: auto;
}

.bot-msg {
    background-color: #1f2937;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 10px 0;
    width: fit-content;
}

.typing {
    color: #9ca3af;
    font-style: italic;
}

.reset-btn {
    float: right;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# Header
# -----------------------

st.title("🧠 Agentic News Chatbot")
st.write("Ask questions about the dataset.")

# -----------------------
# Reset button
# -----------------------

if st.button("Reset Chat"):
    st.session_state.messages = []
    st.rerun()

# -----------------------
# Session state
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
# Input
# -----------------------

prompt = st.chat_input("Ask a question about the dataset...")

if prompt:

    # show user message
    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.markdown(
        f'<div class="user-msg">{prompt}</div>',
        unsafe_allow_html=True
    )

    # typing indicator
    thinking = st.empty()
    thinking.markdown(
        '<div class="bot-msg typing">Bot is thinking...</div>',
        unsafe_allow_html=True
    )

    try:

        response = requests.post(
            API_URL,
            json={"question": prompt}
        )

        result = response.json()

        answer = result.get("answer", "No response received.")

    except Exception as e:

        answer = f"Error contacting API: {e}"

    time.sleep(0.5)

    thinking.empty()

    st.session_state.messages.append({
        "role": "assistant",
        "content": answer
    })

    st.markdown(
        f'<div class="bot-msg">{answer}</div>',
        unsafe_allow_html=True
    )