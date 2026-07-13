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

function buildConversation(title = "New Conversation") {
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

function MessageBubble({ role, text }) {
  const isUser = role === "user";

  return (
    <div className={`message-row ${isUser ? "user" : "ai"}`}>
      <div className={`avatar ${isUser ? "user-avatar" : "ai-avatar"}`}>
        {isUser ? "You" : "AI"}
      </div>
      <div className="message-bubble">
        <div className="message-sender">{isUser ? "You" : "MedAssist"}</div>
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
  const messagesEndRef = useRef(null);

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
  };

  const clearActiveConversation = () => {
    updateActiveConversation((item) => ({ ...item, title: "New Conversation", messages: [] }));
  };

  const handleSend = async (customText) => {
    const message = (customText ?? input).trim();
    if (!message || isSending || !activeConversation) return;

    setInput("");
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
    <div className="layout">
      <aside className="sidebar">
        <div className="logo-block">
          <h1>MedAssist</h1>
          <p>RAG + Groq</p>
        </div>

        <button className="action-btn" onClick={createConversation}>
          New Conversation
        </button>

        <div className="history-list">
          {conversations.map((item) => (
            <button
              key={item.id}
              className={`history-item ${item.id === activeConversation?.id ? "active" : ""}`}
              onClick={() => setActiveConversationId(item.id)}
            >
              {item.title}
            </button>
          ))}
        </div>

        <button
          className="theme-btn"
          onClick={() => setTheme((prev) => (prev === "light" ? "dark" : "light"))}
        >
          {theme === "light" ? "Switch To Dark" : "Switch To Light"}
        </button>
      </aside>

      <main className="chat-panel">
        <header className="topbar">
          <div>
            <h2>{activeConversation?.title || "New Conversation"}</h2>
            <p>
              Model: Groq · Status: {backendStatus}
            </p>
          </div>
          <button className="ghost-btn" onClick={clearActiveConversation}>
            Clear Chat
          </button>
        </header>

        <section className="messages">
          {activeConversation?.messages.length ? (
            activeConversation.messages.map((msg, idx) => (
              <MessageBubble key={`${msg.ts}-${idx}`} role={msg.role} text={msg.text} />
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
              <div className="avatar ai-avatar">AI</div>
              <div className="message-bubble">
                <div className="message-sender">MedAssist</div>
                <div className="message-text">Thinking...</div>
              </div>
            </div>
          ) : null}
          <div ref={messagesEndRef} />
        </section>

        <footer className="composer">
          <textarea
            placeholder="Describe symptoms or ask a medical question..."
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                handleSend();
              }
            }}
          />
          <button className="send-btn" onClick={() => handleSend()} disabled={!input.trim() || isSending}>
            Send
          </button>
        </footer>
      </main>
    </div>
  );
}
