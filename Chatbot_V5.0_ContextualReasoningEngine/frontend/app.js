/* =========================
   STATE
========================= */
const emptyState      = document.getElementById("emptyState");
const chatContainer   = document.getElementById("chatContainer");
const messages        = document.getElementById("messages");
const recentsContainer= document.getElementById("recents");
const inputCenter     = document.getElementById("inputCenter");
const inputBottom     = document.getElementById("inputBottom");

let chats          = [];
let currentChat    = [];
let started        = false;
let isExistingChat = false;
let activeChatIndex= null;
let isGenerating   = false;
let controller     = null;
let recentsVisible = true;


/* =========================
   AUTO-RESIZE TEXTAREA
========================= */
function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}


/* =========================
   KEYBOARD HANDLERS
========================= */
function handleCenterKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendMessageCenter();
  }
}

function handleBottomKey(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    handleSend();
  }
}



/* =========================
   FORMAT BOT RESPONSE
========================= */
function formatResponse(text) {
  // Server sends HTML strings — normalize <br> tags to real line breaks,
  // then re-render with styled wrappers for bullets and spacing

  let html = text;

  // Normalize all <br> variants to newline
  html = html.replace(/<br\s*\/?>/gi, "\n");

  // Split into lines and build styled output
  const lines = html.split("\n");
  let result = "";

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    if (line === "") {
      result += '<div class="resp-spacer"></div>';
    } else if (line.startsWith("•")) {
      result += `<div class="resp-bullet">${line.slice(1).trim()}</div>`;
    } else {
      result += `<div class="resp-line">${line}</div>`;
    }
  }

  return result;
}


/* =========================
   START CHAT
========================= */
function startChat() {
  if (!started) {
    started = true;
    emptyState.classList.add("hidden");
    chatContainer.classList.remove("hidden");
  }
}


/* =========================
   SEND / STOP TOGGLE
========================= */
function handleSend() {
  if (isGenerating) {
    stopGeneration();
  } else {
    sendMessageBottom();
  }
}


/* =========================
   SEND (CENTER)
========================= */
function sendMessageCenter() {
  const text = inputCenter.value.trim();
  if (!text) return;
  startChat();
  inputCenter.value = "";
  inputCenter.style.height = "auto";
  handleMessage(text);
}


/* =========================
   SEND (BOTTOM)
========================= */
function sendMessageBottom() {
  const text = inputBottom.value.trim();
  if (!text) return;
  inputBottom.value = "";
  inputBottom.style.height = "auto";
  handleMessage(text);
}


/* =========================
   CORE MESSAGE HANDLER
========================= */
async function handleMessage(text) {

  // Ensure chat UI is visible
  startChat();

  // Create new chat slot if first message
  if (!isExistingChat && currentChat.length === 0) {
    chats.unshift([]);
    activeChatIndex = 0;
    isExistingChat = true;
  }

  // Render user bubble
  addMessage(text, "user");
  currentChat.push({ type: "user", text });
  chats[activeChatIndex] = [...currentChat];
  renderRecents();

  // Switch to generating
  isGenerating = true;
  updateSendBtn();

  // Typing indicator
  const loadingBubble = addTypingIndicator();

  controller = new AbortController();

  try {
    const res = await fetch("http://127.0.0.1:8001/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: text }),
      signal: controller.signal
    });

    const data = await res.json();

    if (!isGenerating) return;

    loadingBubble.parentElement.remove(); // remove the whole row
    const botBubble = addMessage(data.answer, "bot");

    scrollToBottom();
    setTimeout(scrollToBottom, 60);

    currentChat.push({ type: "bot", text: data.answer });
    if (isExistingChat && activeChatIndex !== null) {
      chats[activeChatIndex] = [...currentChat];
    }

  } catch (err) {
    loadingBubble.parentElement.remove();

    if (err.name === "AbortError") {
      addStatusMessage("Generation stopped.");
    } else {
      addStatusMessage("⚠ Could not reach the server.");
    }
  }

  isGenerating = false;
  updateSendBtn();
}


/* =========================
   STOP
========================= */
function stopGeneration() {
  if (controller) controller.abort();
  isGenerating = false;
  updateSendBtn();
}


/* =========================
   BUTTON STATE
========================= */
function updateSendBtn() {
  const btn = document.getElementById("sendBtn");
  const icon = document.getElementById("sendIcon");
  if (!btn) return;

  if (isGenerating) {
    btn.classList.add("stop");
    btn.innerHTML = `<div class="stop-square"></div>`;
  } else {
    btn.classList.remove("stop");
    btn.innerHTML = `
      <svg id="sendIcon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
        <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
      </svg>`;
  }
}


/* =========================
   ADD USER / BOT MESSAGE
========================= */
function addMessage(text, type) {
  const row = document.createElement("div");
  row.classList.add("message-row", type);

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");

  if (type === "bot") {
    bubble.innerHTML = formatResponse(text);
  } else {
    bubble.textContent = text;
  }

  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();
  return bubble;
}


/* =========================
   TYPING INDICATOR
========================= */
function addTypingIndicator() {
  const row = document.createElement("div");
  row.classList.add("message-row", "bot");

  const bubble = document.createElement("div");
  bubble.classList.add("bubble");
  bubble.innerHTML = `<div class="typing-dots"><span></span><span></span><span></span></div>`;

  row.appendChild(bubble);
  messages.appendChild(row);
  scrollToBottom();
  return bubble;
}


/* =========================
   STATUS MESSAGE
========================= */
function addStatusMessage(text) {
  const row = document.createElement("div");
  row.style.cssText = "display:flex;justify-content:center;padding:6px 0;";

  const el = document.createElement("div");
  el.style.cssText = "font-size:12px;color:#555;background:#161616;border:1px solid #1f1f1f;padding:4px 12px;border-radius:99px;";
  el.textContent = text;

  row.appendChild(el);
  messages.appendChild(row);
  scrollToBottom();
}


/* =========================
   SCROLL
========================= */
function scrollToBottom() {
  requestAnimationFrame(() => {
    const container = document.getElementById("chatContainer");
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
    }
  });
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
    if (index === activeChatIndex) div.classList.add("active");

    const first = chat.find(m => m.type === "user");
    div.textContent = first
      ? first.text.slice(0, 32) + (first.text.length > 32 ? "…" : "")
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
  currentChat.forEach(msg => addMessage(msg.text, msg.type));

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
  const sidebar = document.getElementById("sidebar");
  const collapsed = sidebar.classList.toggle("collapsed");

  if (collapsed) {
    recentsContainer.style.display = "none";
    document.getElementById("recentsArrow")?.classList.add("rotated");
    recentsVisible = false;
  }
}


/* =========================
   RECENTS TOGGLE
========================= */
function toggleRecents() {
  recentsVisible = !recentsVisible;
  const arrow = document.getElementById("recentsArrow");

  if (recentsVisible) {
    recentsContainer.style.display = "flex";
    arrow?.classList.remove("rotated");
  } else {
    recentsContainer.style.display = "none";
    arrow?.classList.add("rotated");
  }
}

function handleRecentsClick() {
  const sidebar = document.getElementById("sidebar");

  if (sidebar.classList.contains("collapsed")) {
    sidebar.classList.remove("collapsed");
    recentsContainer.style.display = "flex";
    document.getElementById("recentsArrow")?.classList.remove("rotated");
    recentsVisible = true;
  } else {
    toggleRecents();
  }
}