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
# Session State
# -----------------------

if "messages" not in st.session_state:
    st.session_state.messages = []

if "history" not in st.session_state:
    st.session_state.history = []

if "titles" not in st.session_state:
    st.session_state.titles = []

# -----------------------
# Sidebar
# -----------------------

with st.sidebar:

    st.title("⚙️ Controls")

    if st.button("🔄 Reset Chat"):

        if st.session_state.messages:

            first_question = None

            for m in st.session_state.messages:
                if m["role"] == "user":
                    first_question = m["content"]
                    break

            if first_question:
                title = first_question[:40] + ("..." if len(first_question) > 40 else "")
            else:
                title = "New Chat"

            st.session_state.history.append(st.session_state.messages.copy())
            st.session_state.titles.append(title)

        st.session_state.messages = []

        st.rerun()

    st.markdown("---")

    st.markdown("### 💬 Previous Chats")

    for i in range(len(st.session_state.history) - 1, -1, -1):

        title = st.session_state.titles[i]

        if st.button(f"📂 {title}", key=f"chat_{i}"):

            st.session_state.messages = st.session_state.history[i]

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
    margin: 10px 0 10px auto;
    max-width: 70%;
    width: fit-content;
    line-height: 1.6;
    white-space: pre-line;
}

.bot-msg {
    background-color: #1f2937;
    color: white;
    padding: 12px 16px;
    border-radius: 12px;
    margin: 10px auto 10px 0;
    max-width: 70%;
    width: fit-content;
    line-height: 1.6;
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

    st.session_state.messages.append({
        "role": "user",
        "content": prompt
    })

    st.rerun()

# -----------------------
# Generate Bot Response
# -----------------------

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    question = st.session_state.messages[-1]["content"]

    thinking = st.empty()

    # Thinking animation
    dots = 0
    for _ in range(10):
        thinking.markdown(
            f'<div class="bot-msg typing">Bot is thinking{"." * (dots % 4)}</div>',
            unsafe_allow_html=True
        )
        dots += 1
        time.sleep(0.2)

    try:

        response = requests.post(
            API_URL,
            json={"question": question},
            timeout=180
        )

        result = response.json()

        answer = result.get("answer", "No response received.")

    except Exception as e:

        answer = f"Error contacting API: {e}"

    thinking.empty()

    # Streaming typing effect
    streamed = ""
    placeholder = st.empty()

    for word in answer.split():

        streamed += word + " "

        placeholder.markdown(
            f'<div class="bot-msg">{streamed}</div>',
            unsafe_allow_html=True
        )

        time.sleep(0.03)

    st.session_state.messages.append({
        "role": "assistant",
        "content": streamed
    })

    st.rerun()

# -----------------------
# Auto Scroll
# -----------------------

st.markdown(
    """
    <script>
        window.scrollTo(0, document.body.scrollHeight);
    </script>
    """,
    unsafe_allow_html=True
)