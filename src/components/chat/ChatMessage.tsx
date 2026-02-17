"use client";

import { marked } from "marked";
import type { ChatMessage as ChatMessageType } from "@/types/api";

marked.use({ breaks: true, gfm: true });

const SOURCE_LABELS: Record<string, string> = {
  "open.philgeps.gov.ph": "PhilGEPS",
  "comelec.gov.ph": "COMELEC SOCE",
  "coa.gov.ph": "COA Audit Reports",
  "gppb.gov.ph": "GPPB Blacklist",
  "ombudsman.gov.ph": "Ombudsman SALN",
  "psa.gov.ph": "PSA PSGC",
  "open-congress-api.bettergov.ph": "Open Congress",
};

function getSourceLabel(url: string): string {
  try {
    const hostname = new URL(url).hostname.replace("www.", "");
    return SOURCE_LABELS[hostname] || hostname;
  } catch {
    return url;
  }
}

interface ChatMessageProps {
  message: ChatMessageType;
}

export default function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end py-1.5">
        <div
          className="max-w-[85%] rounded-2xl rounded-br-md px-4 py-2.5"
          style={{
            backgroundColor: "var(--chat-user-bg)",
          }}
        >
          <p
            className="text-sm leading-relaxed"
            style={{ color: "var(--chat-user-text)" }}
          >
            {message.content}
          </p>
        </div>
      </div>
    );
  }

  const html = marked.parse(message.content) as string;

  return (
    <div className="py-1.5">
      <div className="max-w-[95%]">
        {message.content && (
          <div
            className="chat-markdown text-[13px] leading-[1.7]"
            style={{ color: "var(--chat-assistant-text)" }}
            dangerouslySetInnerHTML={{ __html: html }}
          />
        )}
        {message.sources && message.sources.length > 0 && (
          <div
            className="mt-3 flex flex-wrap gap-1.5 border-t pt-2"
            style={{ borderColor: "var(--color-border)" }}
          >
            <span
              className="text-[10px] font-medium uppercase tracking-wider"
              style={{ color: "var(--color-text-muted)" }}
            >
              Sources
            </span>
            {message.sources.map((source, idx) => (
              <a
                key={idx}
                href={source}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center rounded-md px-2 py-0.5 text-[11px] transition-colors hover:opacity-80"
                style={{
                  backgroundColor: "var(--color-input-bg)",
                  color: "var(--color-accent)",
                }}
              >
                {getSourceLabel(source)}
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
