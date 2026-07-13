"use client";

import { useEffect, useMemo, useRef, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "/rag";
const STORE_KEY = "medassist_react_conversations";
const THEME_KEY = "medassist_react_theme";

const SUGGESTIONS = [
  "What are common symptoms of flu?",
  "What are early signs of diabetes?",
  "What causes frequent headaches?",
  "How can I improve sleep quality?",
];

function buildConversation(title = "New conversation") {
  return {
    id: `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`,
    title,
    messages: [],
    createdAt: Date.now(),
  };
}

async function askAssistant(question) {
  const response = await fetch(API_URL, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Backend HTTP ${response.status}`);
  }

  const data = await response.json();
  return data.response || data.answer || "No response returned by backend.";
}

function formatTime(ts) {
  return new Date(ts).toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

/* ---- Icons (inline, currentColor, no icon-font dependency) ---- */
const PlusIcon = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round">
    <path d="M12 5v14M5 12h14" />
  </svg>
);
const SendIcon = () => (
  <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 12l16-7-7 16-2.5-7.5L4 12z" />
  </svg>
);
const SunIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <circle cx="12" cy="12" r="4.2" />
    <path d="M12 2.5v2.4M12 19.1v2.4M4.6 4.6l1.7 1.7M17.7 17.7l1.7 1.7M2.5 12h2.4M19.1 12h2.4M4.6 19.4l1.7-1.7M17.7 6.3l1.7-1.7" />
  </svg>
);
const MoonIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="none">
    <path d="M20.5 14.5A8.5 8.5 0 0 1 9.5 3.5a8.5 8.5 0 1 0 11 11z" />
  </svg>
);
const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M3 12a9 9 0 0 1 15.4-6.4M21 12a9 9 0 0 1-15.4 6.4M18 3v5h-5M6 21v-5h5" />
  </svg>
);
const MenuIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <path d="M4 7h16M4 12h16M4 17h16" />
  </svg>
);
const CloseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round">
    <path d="M6 6l12 12M18 6L6 18" />
  </svg>
);

function MessageBubble({ role, text, ts }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "ai"}`}>
      <div className={`avatar ${isUser ? "user" : "ai"}`} aria-hidden="true">
        {isUser ? "You" : "AI"}
      </div>
      <div className="message-col">
        <div className="message-meta">
          <span className="message-sender">{isUser ? "You" : "MedAssist"}</span>
          <span className="message-time">{formatTime(ts)}</span>
        </div>
        <div className="message-text">{text}</div>
      </div>
    </div>
  );
}

export default function Home() {
  const [theme, setTheme] = useState("light");
  const [conversations, setConversations] = useState([buildConversation()]);
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  useEffect(() => {
    const cachedTheme = localStorage.getItem(THEME_KEY);
    if (cachedTheme) setTheme(cachedTheme);

    const cached = localStorage.getItem(STORE_KEY);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        if (parsed.length) {
          setConversations(parsed);
          setActiveConversationId(parsed[0].id);
        }
      } catch {
        // ignore malformed cache
      }
    }
  }, []);

  useEffect(() => {
    if (!activeConversationId && conversations.length) {
      setActiveConversationId(conversations[0].id);
    }
  }, [activeConversationId, conversations]);

  useEffect(() => {
    localStorage.setItem(STORE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversations, isSending]);

  useEffect(() => {
    let cancelled = false;

    async function pingBackend() {
      try {
        const endpoint = API_URL.startsWith("http")
          ? API_URL.replace(/\/rag$/, "/")
          : "/";
        const response = await fetch(endpoint);
        if (!cancelled) {
          setBackendStatus(response.ok ? "online" : "offline");
        }
      } catch {
        if (!cancelled) {
          setBackendStatus("offline");
        }
      }
    }

    pingBackend();
    return () => {
      cancelled = true;
    };
  }, []);

  const activeConversation = useMemo(
    () => conversations.find((item) => item.id === activeConversationId) || conversations[0],
    [activeConversationId, conversations]
  );

  const updateActiveConversation = (updater) => {
    setConversations((prev) =>
      prev.map((item) => (item.id === activeConversation.id ? updater(item) : item))
    );
  };

  const createConversation = () => {
    const next = buildConversation();
    setConversations((prev) => [next, ...prev]);
    setActiveConversationId(next.id);
    setSidebarOpen(false);
  };

  const clearActiveConversation = () => {
    updateActiveConversation((item) => ({ ...item, title: "New conversation", messages: [] }));
  };

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  const handleSend = async (customText) => {
    const message = (customText ?? input).trim();
    if (!message || isSending || !activeConversation) return;

    setInput("");
    requestAnimationFrame(autoResize);
    setIsSending(true);

    const userMessage = { role: "user", text: message, ts: Date.now() };

    updateActiveConversation((item) => {
      const title = item.messages.length
        ? item.title
        : message.length > 42
          ? `${message.slice(0, 42)}...`
          : message;
      return { ...item, title, messages: [...item.messages, userMessage] };
    });

    try {
      const reply = await askAssistant(message);
      const aiMessage = { role: "ai", text: reply, ts: Date.now() };
      updateActiveConversation((item) => ({
        ...item,
        messages: [...item.messages, aiMessage],
      }));
      setBackendStatus("online");
    } catch (error) {
      const aiMessage = {
        role: "ai",
        text: "Sorry, I cannot reach the backend right now. Make sure FastAPI is running on port 8000.",
        ts: Date.now(),
      };
      updateActiveConversation((item) => ({
        ...item,
        messages: [...item.messages, aiMessage],
      }));
      setBackendStatus("offline");
      console.error(error);
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div className="app">
      <div
        className={`scrim ${sidebarOpen ? "open" : ""}`}
        onClick={() => setSidebarOpen(false)}
        aria-hidden="true"
      />

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand">
          <div className="brand-mark">M</div>
          <div className="brand-text">
            <h1>MedAssist</h1>
            <p>Hybrid RAG + Groq</p>
          </div>
          <button
            className="icon-btn mobile-close"
            style={{ marginLeft: "auto" }}
            onClick={() => setSidebarOpen(false)}
            aria-label="Close menu"
          >
            <CloseIcon />
          </button>
        </div>

        <button className="new-chat-btn" onClick={createConversation}>
          <PlusIcon />
          New conversation
        </button>

        <div className="rail-label">History</div>
        <div className="history-list">
          {conversations.map((item) => (
            <button
              key={item.id}
              className={`history-item ${item.id === activeConversation?.id ? "active" : ""}`}
              onClick={() => {
                setActiveConversationId(item.id);
                setSidebarOpen(false);
              }}
            >
              {item.title}
            </button>
          ))}
        </div>

        <div className="sidebar-footer">
          <button
            className="theme-toggle"
            onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
            aria-label={theme === "light" ? "Switch to dark theme" : "Switch to light theme"}
          >
            {theme === "light" ? <MoonIcon /> : <SunIcon />}
            {theme === "light" ? "Dark" : "Light"}
          </button>
        </div>
      </aside>

      <main className="chat-panel">
        <header className="topbar">
          <button
            className="icon-btn menu-btn"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open menu"
          >
            <MenuIcon />
          </button>

          <div className="topbar-title">
            <h2>{activeConversation?.title || "New conversation"}</h2>
            <span className="status-pill">
              <span className={`status-dot ${backendStatus}`} aria-hidden="true" />
              <span className="status-model">Groq · llama-3.3-70b · </span>
              {backendStatus}
            </span>
          </div>

          <div className="topbar-actions">
            <button className="icon-btn" onClick={clearActiveConversation} aria-label="Clear conversation">
              <RefreshIcon />
              <span className="btn-label">Clear</span>
            </button>
          </div>
        </header>

        <section className="messages" aria-live="polite">
          {activeConversation?.messages.length ? (
            activeConversation.messages.map((msg, idx) => (
              <MessageBubble key={`${msg.ts}-${idx}`} role={msg.role} text={msg.text} ts={msg.ts} />
            ))
          ) : (
            <div className="welcome">
              <h3>Ask a medical question</h3>
              <p>
                The assistant retrieves context from Pinecone and generates an answer with Groq.
              </p>
              <div className="suggestions">
                {SUGGESTIONS.map((item) => (
                  <button key={item} className="chip" onClick={() => handleSend(item)}>
                    {item}
                  </button>
                ))}
              </div>
            </div>
          )}

          {isSending ? (
            <div className="message-row ai">
              <div className="avatar ai" aria-hidden="true">AI</div>
              <div className="message-col">
                <div className="message-meta">
                  <span className="message-sender">MedAssist</span>
                </div>
                <div className="message-text">
                  <span className="typing-dots" aria-label="MedAssist is typing">
                    <span />
                    <span />
                    <span />
                  </span>
                </div>
              </div>
            </div>
          ) : null}
          <div ref={messagesEndRef} />
        </section>

        <footer className="composer">
          <div className="composer-inner">
            <textarea
              ref={textareaRef}
              rows={1}
              placeholder="Describe symptoms or ask a medical question..."
              value={input}
              onChange={(event) => {
                setInput(event.target.value);
                autoResize();
              }}
              onKeyDown={(event) => {
                if (event.key === "Enter" && !event.shiftKey) {
                  event.preventDefault();
                  handleSend();
                }
              }}
              aria-label="Message MedAssist"
            />
            <button
              className="send-btn"
              onClick={() => handleSend()}
              disabled={!input.trim() || isSending}
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
          <p className="composer-hint">MedAssist can make mistakes. Verify important medical information.</p>
        </footer>
      </main>
    </div>
  );
}
