"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { PaperPlaneRight, X, Key } from "@phosphor-icons/react";
import type { ChatMessage as ChatMessageType } from "@/types/api";
import type { GraphData } from "@/types/graph";
import { streamChat } from "@/lib/api";
import ChatMessage from "./ChatMessage";
import SuggestedQuestions from "./SuggestedQuestions";
import ApiKeyModal from "@/components/common/ApiKeyModal";
import { INSIGHT_BANNERS } from "@/lib/constants";

const API_KEY_STORAGE = "papertrail-api-key";

interface ChatPanelProps {
  onClose: () => void;
  onGraphContext?: (context: GraphData) => void;
  focusedNodeId?: string;
  visibleNodeIds?: string[];
  initialQuery?: string | null;
  onInitialQueryConsumed?: () => void;
}

function updateLastAssistant(
  prev: ChatMessageType[],
  updater: (msg: ChatMessageType) => ChatMessageType,
): ChatMessageType[] {
  return prev.map((msg, i) => {
    if (i === prev.length - 1 && msg.role === "assistant") {
      return updater(msg);
    }
    return msg;
  });
}

export default function ChatPanel({
  onClose,
  onGraphContext,
  focusedNodeId,
  visibleNodeIds,
  initialQuery,
  onInitialQueryConsumed,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessageType[]>([]);
  const [input, setInput] = useState("");
  const [isStreaming, setIsStreaming] = useState(false);
  const [showKeyModal, setShowKeyModal] = useState(false);
  const [apiKey, setApiKey] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // restore key from sessionStorage on mount
  useEffect(() => {
    const stored = sessionStorage.getItem(API_KEY_STORAGE);
    if (stored) setApiKey(stored);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    // Auto-focus input when panel opens
    const timer = setTimeout(() => inputRef.current?.focus(), 300);
    return () => clearTimeout(timer);
  }, []);

  const pendingMessageRef = useRef<string | null>(null);

  const handleSend = useCallback(
    async (message: string) => {
      if (!message.trim() || isStreaming) return;

      // require API key before first chat
      if (!apiKey) {
        pendingMessageRef.current = message;
        setShowKeyModal(true);
        return;
      }

      const userMessage: ChatMessageType = {
        id: Date.now().toString(),
        role: "user",
        content: message,
        timestamp: new Date().toISOString(),
      };

      const assistantMessage: ChatMessageType = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
      };

      const history = messages
        .filter((m) => m.content.trim())
        .map((m) => ({ role: m.role, content: m.content }));

      setMessages((prev) => [...prev, userMessage, assistantMessage]);
      setInput("");
      setIsStreaming(true);

      try {
        const stream = streamChat(
          message,
          {
            focused_node_id: focusedNodeId,
            visible_node_ids: visibleNodeIds,
            history: [...history, { role: "user", content: message }],
          },
          apiKey,
        );

        const reader = stream.getReader();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          if (typeof value === "string") {
            setMessages((prev) =>
              updateLastAssistant(prev, (msg) => ({
                ...msg,
                content: msg.content + value,
              })),
            );
          } else if (typeof value === "object" && value !== null) {
            const obj = value as Record<string, unknown>;
            if (obj.content && typeof obj.content === "string") {
              setMessages((prev) =>
                updateLastAssistant(prev, (msg) => ({
                  ...msg,
                  content: msg.content + obj.content,
                })),
              );
            }
            if (obj.graph_context && onGraphContext) {
              onGraphContext(obj.graph_context as GraphData);
            }
            if (obj.sources && Array.isArray(obj.sources)) {
              setMessages((prev) =>
                updateLastAssistant(prev, (msg) => ({
                  ...msg,
                  sources: obj.sources as string[],
                })),
              );
            }
          }
        }
      } catch (error) {
        console.error("Chat stream error:", error);
        setMessages((prev) =>
          updateLastAssistant(prev, (msg) => ({
            ...msg,
            content: "Sorry, I encountered an error processing your request.",
          })),
        );
      } finally {
        setIsStreaming(false);
      }
    },
    [isStreaming, messages, focusedNodeId, visibleNodeIds, onGraphContext, apiKey],
  );

  // Auto-send when an initial query is provided (e.g. from insight banner)
  const initialQueryRef = useRef<string | null>(null);
  useEffect(() => {
    if (initialQuery && initialQuery !== initialQueryRef.current) {
      initialQueryRef.current = initialQuery;
      const timer = setTimeout(() => {
        handleSend(initialQuery);
        onInitialQueryConsumed?.();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [initialQuery, handleSend, onInitialQueryConsumed]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSend(input);
  };

  const handleKeySubmit = (newKey: string) => {
    sessionStorage.setItem(API_KEY_STORAGE, newKey);
    setApiKey(newKey);
    setShowKeyModal(false);
    // send the message that was pending before the modal appeared
    if (pendingMessageRef.current) {
      const pending = pendingMessageRef.current;
      pendingMessageRef.current = null;
      setTimeout(() => handleSend(pending), 100);
    }
  };

  const handleClearKey = () => {
    sessionStorage.removeItem(API_KEY_STORAGE);
    setApiKey(null);
  };

  return (
    <div className="flex h-full flex-col">
      {showKeyModal && (
        <ApiKeyModal
          onSubmit={handleKeySubmit}
          onClose={() => {
            setShowKeyModal(false);
            pendingMessageRef.current = null;
          }}
        />
      )}

      {/* Header */}
      <div
        className="flex items-center justify-between px-4 py-3"
        style={{ borderBottom: "1px solid var(--color-border)" }}
      >
        <div>
          <h2
            className="text-sm font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Ask about the data
          </h2>
          <p className="mt-0.5 text-[11px]" style={{ color: "var(--color-text-muted)" }}>
            GraphRAG-powered analysis
          </p>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => apiKey ? handleClearKey() : setShowKeyModal(true)}
            className="btn-ghost flex items-center gap-1 px-2 py-1 text-[10px]"
            title={apiKey ? "API key connected. Click to disconnect." : "Connect API key"}
            style={{ color: apiKey ? "var(--color-accent)" : "var(--color-text-muted)" }}
          >
            <Key size={12} weight={apiKey ? "fill" : "regular"} />
            <span className="hidden sm:inline">{apiKey ? "Connected" : "Add key"}</span>
          </button>
          <button onClick={onClose} className="btn-ghost">
            <X size={16} weight="bold" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="custom-scrollbar flex-1 overflow-y-auto px-4 py-4">
        {messages.length === 0 ? (
          <div className="flex h-full flex-col">
            <div className="flex flex-1 flex-col items-center justify-center px-2 text-center">
              <div
                className="mb-4 rounded-2xl p-4"
                style={{ backgroundColor: "var(--color-input-bg)" }}
              >
                <svg
                  width="32"
                  height="32"
                  viewBox="0 0 24 24"
                  fill="none"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" fill="currentColor"/>
                </svg>
              </div>
              <p
                className="text-sm font-medium"
                style={{ color: "var(--color-text-primary)" }}
              >
                Explore the accountability graph
              </p>
              <p className="mt-1 text-xs" style={{ color: "var(--color-text-muted)" }}>
                Ask questions about procurement, contractors, and red flags
              </p>
            </div>
            {/* Insight banners */}
            <div className="mb-3 space-y-1.5 px-1">
              <p
                className="text-[10px] font-semibold uppercase tracking-widest"
                style={{ color: "var(--color-text-muted)" }}
              >
                From the data
              </p>
              {INSIGHT_BANNERS.map((banner, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSend(banner.query)}
                  className="flex w-full items-start gap-2 rounded-lg px-2.5 py-2 text-left text-[11px] leading-snug transition-all duration-200"
                  style={{
                    backgroundColor: banner.type === "risk" || banner.type === "audit"
                      ? "var(--badge-risk-high-bg)"
                      : "var(--color-input-bg)",
                    color: banner.type === "risk" || banner.type === "audit"
                      ? "var(--badge-risk-high-text)"
                      : "var(--color-text-secondary)",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <span className="mt-px flex-shrink-0 text-[10px]">
                    {banner.type === "risk" ? "\u26A0" : banner.type === "audit" ? "\u2691" : banner.type === "pattern" ? "\u21C4" : "\u25B6"}
                  </span>
                  <span>{banner.text}</span>
                </button>
              ))}
            </div>
            <SuggestedQuestions onSelect={handleSend} />
          </div>
        ) : (
          <div className="space-y-1">
            {messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}
            {isStreaming && messages[messages.length - 1]?.content === "" && (
              <div className="flex items-center gap-1.5 px-1 py-3">
                <div
                  className="typing-dot h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: "var(--color-text-muted)" }}
                />
                <div
                  className="typing-dot h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: "var(--color-text-muted)" }}
                />
                <div
                  className="typing-dot h-1.5 w-1.5 rounded-full"
                  style={{ backgroundColor: "var(--color-text-muted)" }}
                />
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-3" style={{ borderTop: "1px solid var(--color-border)" }}>
        <form onSubmit={handleSubmit}>
          <div
            className="flex items-center gap-2 rounded-xl px-3 py-1 transition-all duration-200"
            style={{
              backgroundColor: "var(--color-input-bg)",
              border: "1px solid var(--color-border)",
            }}
          >
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              disabled={isStreaming}
              className="flex-1 bg-transparent py-2 text-sm outline-none disabled:opacity-50"
              style={{
                color: "var(--color-text-primary)",
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-white transition-all duration-200 disabled:opacity-30"
              style={{ backgroundColor: "var(--color-accent)" }}
            >
              <PaperPlaneRight size={14} weight="fill" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
