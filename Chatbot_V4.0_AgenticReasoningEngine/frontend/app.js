const emptyState = document.getElementById("emptyState");
const chatContainer = document.getElementById("chatContainer");
const messages = document.getElementById("messages");
const recentsContainer = document.getElementById("recents");

const inputCenter = document.getElementById("inputCenter");
const inputBottom = document.getElementById("inputBottom");

let chats = [];
let currentChat = [];

let started = false;
let isExistingChat = false;
let activeChatIndex = null;

/* 🔥 NEW STATE (STOP FEATURE) */
let isGenerating = false;
let controller = null;


/* =========================
   CLEAN HTML (format bot output)
========================= */
function cleanHTML(html) {
  return html
    .replace(/<br>/g, "\n")
    .split("\n")
    .filter(line => line.trim() !== "")
    .map(line => `<div>${line}</div>`)
    .join("");
}


/* =========================
   SWITCH TO CHAT MODE
========================= */
function startChat() {
  if (!started) {
    started = true;
    emptyState.classList.add("hidden");
    chatContainer.classList.remove("hidden");
  }
}


/* =========================
   HANDLE SEND / STOP BUTTON
========================= */
function handleSend() {
  if (isGenerating) {
    stopGeneration();
  } else {
    sendMessageBottom();
  }
}


/* =========================
   SEND (CENTER INPUT)
========================= */
function sendMessageCenter() {
  const text = inputCenter.value.trim();
  if (!text) return;

  startChat();
  inputCenter.value = "";

  handleMessage(text);
}


/* =========================
   SEND (BOTTOM INPUT)
========================= */
function sendMessageBottom() {
  const text = inputBottom.value.trim();
  if (!text) return;

  inputBottom.value = "";
  handleMessage(text);
}


/* =========================
   CORE MESSAGE LOGIC (UPDATED)
========================= */
async function handleMessage(text) {

  // ✅ CREATE CHAT IF FIRST MESSAGE
  if (!isExistingChat && currentChat.length === 0) {
    chats.unshift([]);              // create new chat
    activeChatIndex = 0;            // mark as active
    isExistingChat = true;
  }

  // 🔹 Add user message
  addMessage(text, "user");
  currentChat.push({ type: "user", text });

  // 🔥 UPDATE SIDEBAR IMMEDIATELY
  chats[activeChatIndex] = [...currentChat];
  renderRecents();

  // 🔹 Switch to generating mode
  isGenerating = true;
  updateButton();

  // 🔹 Bot typing placeholder
  const loading = addMessage("", "bot");
  loading.classList.add("typing");

  controller = new AbortController();

  try {
    const res = await fetch("http://127.0.0.1:8001/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question: text }),
      signal: controller.signal
    });

    const data = await res.json();

    // 🔥 If stopped → ignore result
    if (!isGenerating) return;

    loading.classList.remove("typing");
    loading.innerHTML = cleanHTML(data.answer);

    // 🔥 scroll twice to ensure full render
    scrollToBottom();
    setTimeout(scrollToBottom, 50);

    currentChat.push({ type: "bot", text: data.answer });

    // Update existing chat
    if (isExistingChat && activeChatIndex !== null) {
      chats[activeChatIndex] = [...currentChat];
    }

  } catch (err) {
    loading.classList.remove("typing");

    if (err.name === "AbortError") {
      loading.innerHTML = "⛔ Stopped";
    } else {
      loading.innerHTML = "Error connecting to server.";
    }
  }

  isGenerating = false;
  updateButton();
}


/* =========================
   STOP GENERATION
========================= */
function stopGeneration() {
  if (controller) {
    controller.abort();
  }

  isGenerating = false;
  updateButton();
}


/* =========================
   BUTTON UI UPDATE
========================= */
function updateButton() {
  const btn = document.getElementById("sendBtn");

  if (!btn) return;

  if (isGenerating) {
    btn.innerHTML = `<div class="stop-icon"></div>`;
    btn.style.background = "#b33a3a";
    btn.style.borderRadius = "12px";
  } else {
    btn.innerHTML = "➤";
    btn.style.background = "#3b36b3";
    btn.style.borderRadius = "50%";
  }
}


/* =========================
   ADD MESSAGE TO UI
========================= */
function addMessage(text, type) {
  const row = document.createElement("div");
  row.classList.add("message-row", type);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  bubble.innerHTML = cleanHTML(text);

  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();

  return bubble;
}


/* =========================
   NEW CHAT
========================= */
function newChat() {

  if (currentChat.length > 0 && !isExistingChat) {
    chats.unshift([...currentChat]);
  }

  currentChat = [];
  isExistingChat = false;
  activeChatIndex = null;

  messages.innerHTML = "";

  emptyState.classList.remove("hidden");
  chatContainer.classList.add("hidden");
  started = false;

  renderRecents();
}


/* =========================
   RECENTS
========================= */
function renderRecents() {
  recentsContainer.innerHTML = "";

  chats.forEach((chat, index) => {
    const div = document.createElement("div");
    div.classList.add("recent-item");

    if (index === activeChatIndex) {
      div.classList.add("active");
    }

    const first = chat.find(m => m.type === "user");

    div.innerText = first
      ? first.text.slice(0, 30) + (first.text.length > 30 ? "..." : "")
      : "New Chat";

    div.onclick = () => loadChat(index);

    recentsContainer.appendChild(div);
  });
}


/* =========================
   LOAD CHAT
========================= */
function loadChat(index) {
  activeChatIndex = index;
  currentChat = [...chats[index]];
  isExistingChat = true;

  messages.innerHTML = "";

  currentChat.forEach(msg => {
    addMessage(msg.text, msg.type);
  });

  startChat();
  renderRecents();
}


/* =========================
   SEARCH
========================= */
function searchChats() {
  alert("Search coming soon 🚀");
}


/* =========================
   SIDEBAR TOGGLE
========================= */
function toggleSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const chatArea = document.querySelector(".chat-area");
  const recents = document.getElementById("recents");
  const arrow = document.getElementById("recentsArrow");

  const collapsed = sidebar.classList.toggle("collapsed");
  chatArea.classList.toggle("sidebar-collapsed");

  // 🔥 WHEN COLLAPSING → ALWAYS RESET RECENTS
  if (collapsed) {
    recents.style.display = "none";
    arrow.classList.add("rotated");
    recentsVisible = false;
  }
}


/* =========================
   ENTER KEY
========================= */
inputCenter.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessageCenter();
});

inputBottom.addEventListener("keypress", function (e) {
  if (e.key === "Enter") handleSend();
});

let recentsVisible = true;

function toggleRecents() {
  const recents = document.getElementById("recents");
  const arrow = document.getElementById("recentsArrow");

  recentsVisible = !recentsVisible;

  if (recentsVisible) {
    recents.style.display = "flex";
    arrow.classList.remove("rotated");
  } else {
    recents.style.display = "none";
    arrow.classList.add("rotated");
  }
}

function handleRecentsClick() {
  const sidebar = document.querySelector(".sidebar");
  const recents = document.getElementById("recents");
  const arrow = document.getElementById("recentsArrow");

  // ✅ If collapsed → open sidebar + expand recents
  if (sidebar.classList.contains("collapsed")) {
    sidebar.classList.remove("collapsed");

    recents.style.display = "flex";
    arrow.classList.remove("rotated");

    recentsVisible = true;
  } else {
    // otherwise just toggle
    toggleRecents();
  }
}

function scrollToBottom() {
  const messages = document.getElementById("messages");

  // 🔥 wait for DOM render
  requestAnimationFrame(() => {
    messages.scrollTo({
      top: messages.scrollHeight,
      behavior: "smooth"
    });
  });
}