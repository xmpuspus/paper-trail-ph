"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { MagnifyingGlass, X } from "@phosphor-icons/react";
import { searchEntities } from "@/lib/api";
import type { SearchResult } from "@/types/api";
import SearchResults from "./SearchResults";

interface SearchBarProps {
  onSelect: (nodeId: string) => void;
}

export default function SearchBar({ onSelect }: SearchBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [loading, setLoading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout>();

  const handleSearch = useCallback(async (searchQuery: string) => {
    if (!searchQuery.trim()) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    setLoading(true);
    try {
      const response = await searchEntities(searchQuery);
      setResults(response.results || []);
      setIsOpen(true);
    } catch (error) {
      console.error("Search failed:", error);
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    if (query.trim()) {
      timeoutRef.current = setTimeout(() => handleSearch(query), 300);
    } else {
      setResults([]);
      setIsOpen(false);
    }

    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
    };
  }, [query, handleSearch]);

  const handleSelect = useCallback((nodeId: string) => {
    onSelect(nodeId);
    setQuery("");
    setIsOpen(false);
    setSelectedIndex(-1);
    inputRef.current?.blur();
  }, [onSelect]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "/" && document.activeElement !== inputRef.current) {
        e.preventDefault();
        inputRef.current?.focus();
      }

      if (!isOpen) return;

      if (e.key === "Escape") {
        setIsOpen(false);
        setQuery("");
        inputRef.current?.blur();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.min(prev + 1, results.length - 1));
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => Math.max(prev - 1, 0));
      } else if (e.key === "Enter" && selectedIndex >= 0 && results[selectedIndex]) {
        e.preventDefault();
        handleSelect(results[selectedIndex].id);
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, results, selectedIndex, handleSelect]);

  const handleClear = () => {
    setQuery("");
    setResults([]);
    setIsOpen(false);
    setSelectedIndex(-1);
  };

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlass
          size={16}
          className="absolute left-3 top-1/2 -translate-y-1/2"
          style={{ color: "var(--color-text-muted)" }}
        />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder="Search entities..."
          className="search-input py-2 pl-9 pr-16"
        />
        <div className="absolute right-3 top-1/2 flex -translate-y-1/2 items-center gap-1.5">
          {query ? (
            <button
              onClick={handleClear}
              className="transition-colors"
              style={{ color: "var(--color-text-muted)" }}
            >
              <X size={14} />
            </button>
          ) : (
            <kbd
              className="hidden rounded-md px-1.5 py-0.5 text-[10px] sm:inline"
              style={{
                border: "1px solid var(--color-border)",
                backgroundColor: "var(--color-input-bg)",
                color: "var(--color-text-muted)",
              }}
            >
              /
            </kbd>
          )}
        </div>
      </div>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
          <div
            className="absolute left-0 right-0 top-full z-50 mt-1.5 overflow-hidden rounded-xl backdrop-blur-xl"
            style={{
              backgroundColor: "var(--glass-bg-elevated)",
              border: "1px solid var(--glass-border-elevated)",
              boxShadow: "var(--glass-shadow-elevated)",
            }}
          >
            {loading ? (
              <div
                className="p-4 text-center text-xs"
                style={{ color: "var(--color-text-muted)" }}
              >
                Searching...
              </div>
            ) : (
              <SearchResults
                results={results}
                onSelect={handleSelect}
                selectedIndex={selectedIndex}
              />
            )}
          </div>
        </>
      )}
    </div>
  );
}
