import React, { useState, useRef, useEffect, useContext } from "react";
import { AuthContext } from "../context/AuthContext";
import "./ChatWidget.css";
import API_BASE from "../utils/api";

const SUGGESTIONS = [
  "Which repo should I lead with on my resume?",
  "What's the biggest gap blocking my promotion?",
  "How can I improve my code quality?",
  "Give me a study plan for this week",
];

/* ---- SVG icons ---- */
const BotIcon = () => (
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 2a2 2 0 0 1 2 2c0 .74-.4 1.39-1 1.73V7h1a7 7 0 0 1 7 7v1a3 3 0 0 1-3 3h-1v1a3 3 0 0 1-3 3H10a3 3 0 0 1-3-3v-1H6a3 3 0 0 1-3-3v-1a7 7 0 0 1 7-7h1V5.73A2 2 0 0 1 12 2zM9.5 13a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3zm5 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3z"/>
  </svg>
);

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <path d="M18 6L6 18M6 6l12 12"/>
  </svg>
);

const SendIcon = () => (
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
  </svg>
);

const SourceIcon = () => (
  <svg viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg">
    <path d="M4 1h8a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2zm1 3v1.5h6V4H5zm0 3v1.5h6V7H5zm0 3v1.5h4V10H5z"/>
  </svg>
);

const SparkleIcon = () => (
  <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 1l2.09 6.26L20.35 9.27l-5.09 3.9L16.91 20 12 16.27 7.09 20l1.64-6.83L3.65 9.27l6.26-2.01z"/>
  </svg>
);

/* ---- Simple markdown-ish renderer ---- */
function renderMarkdown(text) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");
  // Bullet lists
  html = html.replace(/^[-•] (.+)$/gm, "<li>$1</li>");
  html = html.replace(/(<li>.*<\/li>\n?)+/gs, (match) => `<ul>${match}</ul>`);
  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, "<li>$1</li>");
  // Line breaks
  html = html.replace(/\n/g, "<br/>");
  return html;
}

export default function ChatWidget() {
  const { token, user } = useContext(AuthContext);
  const [open, setOpen] = useState(false);
  const [closing, setClosing] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [convId, setConvId] = useState(null);
  const [error, setError] = useState(null);
  const [rateLimit, setRateLimit] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus input when opened
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 350);
    }
  }, [open]);

  const handleClose = () => {
    setClosing(true);
    setTimeout(() => {
      setOpen(false);
      setClosing(false);
    }, 240);
  };

  const handleToggle = () => {
    if (open) handleClose();
    else setOpen(true);
  };

  const sendMessage = async (text) => {
    if (!text.trim() || loading || !token) return;

    const userMsg = {
      role: "user",
      content: text.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: text.trim(),
          conversation_id: convId,
        }),
      });

      if (res.status === 429) {
        const data = await res.json();
        setError(data.detail || "Rate limit exceeded. Please wait.");
        setLoading(false);
        return;
      }

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Error ${res.status}`);
      }

      const data = await res.json();
      setConvId(data.conversation_id);
      if (data.rate_limit) setRateLimit(data.rate_limit);

      const aiMsg = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        sources: data.sources || [],
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (e) {
      const errMsg = e.message || "Failed to send message";
      if (errMsg.includes("fetch") || errMsg.includes("network") || errMsg.includes("Failed")) {
        setError("Can't reach the server. Make sure the backend is running.");
      } else {
        setError(errMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(input);
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  };

  // Don't render if not logged in
  if (!token) return null;

  return (
    <>
      {/* Floating Action Button */}
      <button
        className={`chat-fab ${open ? "open" : ""}`}
        onClick={handleToggle}
        aria-label="Chat with DevCareer Coach"
        id="chat-fab"
      >
        {open ? <CloseIcon /> : <BotIcon />}
      </button>

      {/* Chat Window */}
      {open && (
        <div className={`chat-window ${closing ? "closing" : ""}`} role="dialog" aria-label="DevCareer Coach Chat">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-avatar">
              <BotIcon />
            </div>
            <div className="chat-header-info">
              <div className="chat-header-title">DevCareer Coach</div>
              <div className="chat-header-status">
                <span className="chat-status-dot" />
                Ask anything about your repos & career
              </div>
            </div>
            <button className="chat-header-close" onClick={handleClose} aria-label="Close chat">
              <CloseIcon />
            </button>
          </div>

          {/* Messages */}
          <div className="chat-messages">
            {messages.length === 0 && !loading && (
              <div className="chat-empty">
                <div className="chat-empty-icon">
                  <SparkleIcon />
                </div>
                <div className="chat-empty-title">Hey{user?.email ? `, ${user.email.split("@")[0]}` : ""}! 👋</div>
                <div className="chat-empty-desc">
                  I know everything about your code audits. Ask me about your repos, career gaps, resume tips, or learning plans.
                </div>
                <div className="chat-suggestions">
                  <div className="chat-suggestions-label">Try asking</div>
                  {SUGGESTIONS.map((q, i) => (
                    <button
                      key={i}
                      className="chat-suggestion-btn"
                      onClick={() => sendMessage(q)}
                    >
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg, i) => (
              <div key={i} className={`chat-msg ${msg.role}`}>
                <div className="chat-msg-avatar">
                  {msg.role === "assistant" ? "🤖" : "👤"}
                </div>
                <div>
                  <div
                    className="chat-msg-bubble"
                    dangerouslySetInnerHTML={{
                      __html: renderMarkdown(msg.content),
                    }}
                  />
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="chat-sources">
                      {msg.sources.map((src, j) => (
                        <span key={j} className="chat-source-chip" title={src.detail}>
                          <SourceIcon />
                          {src.repo_name || src.type}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-typing">
                <div className="chat-msg-avatar" style={{ background: "linear-gradient(135deg, #6c5ce7, #a855f7)", borderRadius: 10, width: 30, height: 30, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  🤖
                </div>
                <div className="chat-typing-dots">
                  <div className="chat-typing-dot" />
                  <div className="chat-typing-dot" />
                  <div className="chat-typing-dot" />
                </div>
              </div>
            )}

            {error && <div className="chat-error">{error}</div>}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="chat-input-area">
            <form className="chat-input-wrap" onSubmit={handleSubmit}>
              <textarea
                ref={inputRef}
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask about your repos, career, resume..."
                rows={1}
                maxLength={2000}
                disabled={loading}
              />
              <button
                type="submit"
                className="chat-send-btn"
                disabled={!input.trim() || loading}
                aria-label="Send message"
              >
                <SendIcon />
              </button>
            </form>
            {rateLimit && rateLimit.per_minute <= 5 && (
              <div className="chat-rate-warn">
                ⚡ {rateLimit.per_minute} messages remaining this minute
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
