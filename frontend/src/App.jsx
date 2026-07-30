import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_ENDPOINT = "/api/chat/chat"; // proxied to the FastAPI backend by Vite in dev

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "bot",
      text: "Ask me anything about our internal docs — refund policy, onboarding, support hours, and more.",
      sources: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, isLoading]);

  async function handleSubmit(e) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isLoading) return;

    setMessages((prev) => [...prev, { role: "user", text: question }]);
    setInput("");
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch(API_ENDPOINT, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
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
    } catch (err) {
      setError(err.message);
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

  return (
    <div className="shell">
      <header className="topbar">
        <div className="mark">KB</div>
        <div className="titles">
          <h1>Knowledge Base Assistant</h1>
          <p>Answers grounded in your company documents</p>
        </div>
      </header>

      <main className="thread" ref={scrollRef}>
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
              {s.source.split("/").pop()}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}