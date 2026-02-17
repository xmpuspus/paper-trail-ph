"use client";

import { SUGGESTED_QUESTIONS } from "@/lib/constants";

interface SuggestedQuestionsProps {
  onSelect: (question: string) => void;
}

export default function SuggestedQuestions({ onSelect }: SuggestedQuestionsProps) {
  return (
    <div className="space-y-2 pb-2">
      <p
        className="px-1 text-[11px] font-medium uppercase tracking-wider"
        style={{ color: "var(--color-text-muted)" }}
      >
        Try asking
      </p>
      <div className="grid gap-1.5">
        {SUGGESTED_QUESTIONS.slice(0, 6).map((question, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(question)}
            className="rounded-xl px-3 py-2.5 text-left text-xs leading-relaxed transition-all duration-200"
            style={{
              backgroundColor: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-secondary)",
            }}
          >
            {question}
          </button>
        ))}
      </div>
    </div>
  );
}
