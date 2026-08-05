import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_BASE = "/api";

export default function App() {
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isBooting, setIsBooting] = useState(true);
  const scrollRef = useRef(null);

  // Load session list on first mount, then select the most recent one (or create one)
  useEffect(() => {
    (async () => {
      const list = await fetchSessions();
      if (list.length > 0) {
        await selectSession(list[0].id, list);
      } else {
        await createNewChat(list);
      }
      setIsBooting(false);
    })();
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  async function fetchSessions() {
    const res = await fetch(`${API_BASE}/sessions`);
    const data = await res.json();
    setSessions(data);
    return data;
  }

  async function createNewChat(existingList) {
    const res = await fetch(`${API_BASE}/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title: "New Chat" }),
    });
    const session = await res.json();
    setSessions([session, ...(existingList ?? sessions)]);
    setCurrentSessionId(session.id);
    setMessages([]);
    setInput("");
  }

  async function selectSession(sessionId, list) {
    setCurrentSessionId(sessionId);
    const res = await fetch(`${API_BASE}/sessions/${sessionId}/messages`);
    if (!res.ok) return;
    const msgs = await res.json();
    setMessages(
      msgs.map((m) => ({
        role: m.role,
        text: m.content,
        sources: m.sources || [],
      }))
    );
  }

  async function deleteSession(sessionId, e) {
    e.stopPropagation();
    if (!confirm("Delete this chat?")) return;

    await fetch(`${API_BASE}/sessions/${sessionId}`, { method: "DELETE" });
    const updated = sessions.filter((s) => s.id !== sessionId);
    setSessions(updated);

    if (sessionId === currentSessionId) {
      if (updated.length > 0) {
        selectSession(updated[0].id, updated);
      } else {
        createNewChat(updated);
      }
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading || !currentSessionId) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, session_id: currentSessionId }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.detail || `Request failed (${res.status})`);
      }

      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: data.answer, sources: data.sources || [] },
      ]);

      // Refresh session list so titles/ordering update (first question sets the title)
      fetchSessions();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: "Something went wrong reaching the knowledge base. Check that the backend is running on port 8000.",
          sources: [],
          isError: true,
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  if (isBooting) {
    return <div className="boot-screen">Loading...</div>;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="new-chat-btn" onClick={() => createNewChat()}>
          + New Chat
        </button>
        <div className="session-list">
          {sessions.map((s) => (
            <div
              key={s.id}
              className={`session-item ${s.id === currentSessionId ? "active" : ""}`}
              onClick={() => selectSession(s.id)}
            >
              <span className="session-title">{s.title}</span>
              <button
                className="delete-btn"
                onClick={(e) => deleteSession(s.id, e)}
                title="Delete chat"
              >
                ×
              </button>
            </div>
          ))}
        </div>
      </aside>

      <div className="shell">
        <header className="topbar">
          <div className="mark">KB</div>
          <div className="titles">
            <h1>Knowledge Base Assistant</h1>
            <p>Answers grounded in your company documents</p>
          </div>
        </header>

        <main className="thread" ref={scrollRef}>
          {messages.length === 0 && (
            <div className="bubble bot">
              <p>Ask me anything about our internal docs — refund policy, onboarding, support hours, and more.</p>
            </div>
          )}
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
          {isLoading && (
            <div className="bubble bot pending">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          )}
        </main>

        <form className="composer" onSubmit={handleSubmit}>
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about refunds, onboarding, support hours..."
            disabled={isLoading}
          />
          <button type="submit" disabled={isLoading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}

function MessageBubble({ message }) {
  const { role, text, sources, isError } = message;
  return (
    <div className={`bubble ${role} ${isError ? "error" : ""}`}>
      <p>{text}</p>
      {sources && sources.length > 0 && (
        <div className="sources">
          <span className="sources-label">grounded in</span>
          {sources.map((s, i) => (
            <span className="source-chip" key={i} title={s.snippet}>
              {s.source.split(/[/\\]/).pop()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}