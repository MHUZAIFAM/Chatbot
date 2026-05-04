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
   CORE MESSAGE LOGIC
   ========================= */
async function handleMessage(text) {

  // 🔹 Add user message
  addMessage(text, "user");
  currentChat.push({ type: "user", text });

  // 🔹 Show typing (bot placeholder)
  const loading = addMessage("", "bot");
  loading.classList.add("typing");

  try {
    const res = await fetch("http://127.0.0.1:8001/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ question: text })
    });

    const data = await res.json();

    // 🔹 Replace typing with real response
    loading.classList.remove("typing");
    loading.innerHTML = cleanHTML(data.answer);

    // 🔹 Save bot response
    currentChat.push({ type: "bot", text: data.answer });

    // 🔹 Update existing chat (fix duplication)
    if (isExistingChat && activeChatIndex !== null) {
      chats[activeChatIndex] = [...currentChat];
    }

  } catch (err) {
    loading.classList.remove("typing");
    loading.innerHTML = "Error connecting to server.";
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

  // Clean formatting
  bubble.innerHTML = cleanHTML(text);

  row.appendChild(bubble);
  messages.appendChild(row);

  // Auto scroll
  messages.scrollTop = messages.scrollHeight;

  return bubble;
}


/* =========================
   NEW CHAT
   ========================= */
function newChat() {

  // Save only if it's a fresh chat (avoid duplication)
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
   RENDER RECENTS
   ========================= */
function renderRecents() {
  recentsContainer.innerHTML = "";

  chats.forEach((chat, index) => {
    const div = document.createElement("div");
    div.classList.add("recent-item");

    // Highlight active chat
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
   LOAD EXISTING CHAT
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
   SEARCH (placeholder)
   ========================= */
function searchChats() {
  alert("Search coming soon 🚀");
}


/* =========================
   SIDEBAR TOGGLE
   ========================= */
function toggleSidebar() {
  document.querySelector(".sidebar").classList.toggle("collapsed");
}


/* =========================
   ENTER KEY SUPPORT
   ========================= */
inputCenter.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessageCenter();
});

inputBottom.addEventListener("keypress", function (e) {
  if (e.key === "Enter") sendMessageBottom();
});