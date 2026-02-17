"use client";

import type { SearchResult } from "@/types/api";
import { NODE_COLORS, NODE_LABELS } from "@/lib/constants";
import type { NodeType } from "@/types/graph";

interface SearchResultsProps {
  results: SearchResult[];
  onSelect: (nodeId: string) => void;
  selectedIndex: number;
}

export default function SearchResults({ results, onSelect, selectedIndex }: SearchResultsProps) {
  if (results.length === 0) {
    return (
      <div
        className="p-4 text-center text-xs"
        style={{ color: "var(--color-text-muted)" }}
      >
        No results found
      </div>
    );
  }

  return (
    <div className="custom-scrollbar max-h-80 overflow-y-auto py-1">
      {results.map((result, index) => (
        <button
          key={result.id}
          onClick={() => onSelect(result.id)}
          className="flex w-full items-start gap-3 px-3 py-2.5 text-left transition-colors"
          style={{
            backgroundColor:
              index === selectedIndex
                ? "var(--search-highlight-active-bg)"
                : "transparent",
          }}
        >
          <div
            className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full"
            style={{ backgroundColor: NODE_COLORS[result.type as NodeType] || "#666" }}
          />
          <div className="min-w-0 flex-1">
            <div className="flex items-baseline gap-2">
              <span
                className="text-sm font-medium"
                style={{ color: "var(--color-text-primary)" }}
              >
                {result.name}
              </span>
              <span
                className="text-[11px]"
                style={{ color: "var(--color-text-muted)" }}
              >
                {NODE_LABELS[result.type as NodeType] || result.type}
              </span>
            </div>
            {result.context && (
              <div
                className="mt-0.5 truncate text-[11px]"
                style={{ color: "var(--color-text-muted)" }}
              >
                {result.context}
              </div>
            )}
          </div>
        </button>
      ))}
    </div>
  );
}
