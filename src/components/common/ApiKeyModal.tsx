"use client";

import { useState, useRef, useEffect } from "react";
import { X, Eye, EyeSlash, ShieldCheck } from "@phosphor-icons/react";

interface ApiKeyModalProps {
  onSubmit: (key: string) => void;
  onClose: () => void;
}

export default function ApiKeyModal({ onSubmit, onClose }: ApiKeyModalProps) {
  const [key, setKey] = useState("");
  const [visible, setVisible] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const timer = setTimeout(() => inputRef.current?.focus(), 200);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = key.trim();
    if (trimmed) onSubmit(trimmed);
  };

  const isValid = key.trim().startsWith("sk-");

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 animate-fade-in"
        style={{ backgroundColor: "rgba(0, 0, 0, 0.4)", backdropFilter: "blur(8px)" }}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="glass-panel-elevated relative w-full max-w-md animate-fade-in-up rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="btn-ghost absolute right-3 top-3"
          aria-label="Close"
        >
          <X size={16} weight="bold" />
        </button>

        <div className="p-6">
          {/* Icon */}
          <div
            className="mb-4 inline-flex rounded-2xl p-3"
            style={{ backgroundColor: "var(--color-input-bg)" }}
          >
            <ShieldCheck
              size={28}
              weight="duotone"
              style={{ color: "var(--color-accent)" }}
            />
          </div>

          {/* Title */}
          <h2
            className="text-lg font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Connect your API key
          </h2>
          <p
            className="mt-1.5 text-sm leading-relaxed"
            style={{ color: "var(--color-text-secondary)" }}
          >
            The GraphRAG chat uses Claude to answer questions about the graph.
            Provide your Anthropic API key to enable it.
          </p>

          {/* Form */}
          <form onSubmit={handleSubmit} className="mt-5">
            <label
              className="mb-1.5 block text-xs font-medium"
              style={{ color: "var(--color-text-secondary)" }}
              htmlFor="api-key-input"
            >
              Anthropic API Key
            </label>
            <div className="relative">
              <input
                ref={inputRef}
                id="api-key-input"
                type={visible ? "text" : "password"}
                value={key}
                onChange={(e) => setKey(e.target.value)}
                placeholder="sk-ant-..."
                autoComplete="off"
                spellCheck={false}
                className="search-input py-2.5 pr-10 font-mono text-sm"
              />
              <button
                type="button"
                onClick={() => setVisible(!visible)}
                className="btn-ghost absolute right-1.5 top-1/2 -translate-y-1/2 p-1.5"
                tabIndex={-1}
                aria-label={visible ? "Hide key" : "Show key"}
              >
                {visible ? (
                  <EyeSlash size={16} style={{ color: "var(--color-text-muted)" }} />
                ) : (
                  <Eye size={16} style={{ color: "var(--color-text-muted)" }} />
                )}
              </button>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={!isValid}
              className="mt-4 w-full rounded-xl py-2.5 text-sm font-medium text-white transition-all duration-200 disabled:opacity-40"
              style={{ backgroundColor: "var(--color-accent)" }}
            >
              Connect
            </button>
          </form>

          {/* Privacy notice */}
          <div
            className="mt-4 flex items-start gap-2.5 rounded-xl px-3.5 py-3"
            style={{
              backgroundColor: "var(--color-input-bg)",
              border: "1px solid var(--color-border-subtle)",
            }}
          >
            <ShieldCheck
              size={16}
              weight="bold"
              className="mt-0.5 flex-shrink-0"
              style={{ color: "var(--color-text-muted)" }}
            />
            <p
              className="text-xs leading-relaxed"
              style={{ color: "var(--color-text-muted)" }}
            >
              Your key is stored only in this browser tab and sent directly to the
              Anthropic API. It is never saved on our servers and is cleared when
              you close the tab.
            </p>
          </div>

          {/* Get a key link */}
          <p
            className="mt-3 text-center text-xs"
            style={{ color: "var(--color-text-muted)" }}
          >
            Need a key?{" "}
            <a
              href="https://console.anthropic.com/settings/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="underline underline-offset-2 transition-colors"
              style={{ color: "var(--color-accent)" }}
            >
              Get one from Anthropic
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
