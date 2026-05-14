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

if "current_chat" not in st.session_state:
    st.session_state.current_chat = None

if "show_recents" not in st.session_state:
    st.session_state.show_recents = True

if "active_chat" not in st.session_state:
    st.session_state.active_chat = None


# -----------------------
# Sidebar
# -----------------------

with st.sidebar:

    st.title("⚙️ Controls")

    if st.button("➕ New Chat"):
        st.session_state.messages = []
        st.session_state.current_chat = None
        st.session_state.active_chat = None
        st.rerun()


    st.markdown("---")

    # Recents header
    if len(st.session_state.history) > 0:

        arrow = "▾" if st.session_state.show_recents else "▸"

        if st.button(f"Recents\u2009{arrow}", key="toggle_recents"):
            st.session_state.show_recents = not st.session_state.show_recents
            st.rerun()

    else:
        st.markdown("### Recents")

    # Chat list (collapsible)
    if st.session_state.show_recents:

        for i in range(len(st.session_state.history) - 1, -1, -1):

            title = st.session_state.titles[i]

            is_active = st.session_state.active_chat == i

            if is_active:
                button_type = "primary"
            else:
                button_type = "secondary"

            if st.button(
                    title,
                    key=f"chat_{i}",
                    use_container_width=True,
                    type=button_type
            ):
                st.session_state.messages = st.session_state.history[i]
                st.session_state.active_chat = i

                st.rerun()

    st.markdown("---")
    # st.info("Agentic News Dataset Chatbot")


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


/* sidebar chat buttons */
section[data-testid="stSidebar"] button {

    display: flex;
    align-items: center;
    justify-content: flex-start;

    text-align: left;

    padding-left: 12px;

    border-radius: 10px;

    transition: background-color 0.15s ease;
}

/* hover effect (like ChatGPT) */
section[data-testid="stSidebar"] button:hover {

    background-color: rgba(255,255,255,0.05);
}

/* active chat highlight */
button[kind="primary"] {

    background-color: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
}


/* remove border around Recents toggle */
section[data-testid="stSidebar"] div[data-testid="stButton"]:first-child button {

    border: none;
    background: transparent;
    box-shadow: none;
}

button[key="toggle_recents"] {
    letter-spacing: 0.5px;
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

    # Create chat entry when first question is asked
    if st.session_state.current_chat is None:
        words = prompt.split()
        title = " ".join(words[:5]) + "..." if len(words) > 5 else prompt

        st.session_state.history.append(st.session_state.messages.copy())
        st.session_state.titles.append(title)

        st.session_state.current_chat = len(st.session_state.history) - 1
        st.session_state.active_chat = st.session_state.current_chat

    st.rerun()


# -----------------------
# Generate Bot Response
# -----------------------

if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":

    question = st.session_state.messages[-1]["content"]

    thinking = st.empty()

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

    if st.session_state.current_chat is not None:
        st.session_state.history[st.session_state.current_chat] = st.session_state.messages.copy()

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