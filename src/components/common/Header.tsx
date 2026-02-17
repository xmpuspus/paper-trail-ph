"use client";

import { Faders, ChatCircle, Sun, Moon } from "@phosphor-icons/react";
import SearchBar from "@/components/search/SearchBar";
import { useTheme } from "@/components/common/ThemeProvider";
import clsx from "clsx";

interface HeaderProps {
  onSearchSelect: (nodeId: string) => void;
  onFilterToggle: () => void;
  onChatToggle: () => void;
  showFilters?: boolean;
  showChat?: boolean;
}

export default function Header({
  onSearchSelect,
  onFilterToggle,
  onChatToggle,
  showFilters,
  showChat,
}: HeaderProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <header
      className="sticky top-0 z-50 backdrop-blur-xl"
      style={{
        backgroundColor: "var(--glass-bg)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <div className="flex h-14 items-center justify-between px-4 lg:px-6">
        {/* Logo */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2.5">
            <div className="flex h-6 items-center gap-[3px]">
              <div className="h-full w-[3px] rounded-full bg-[#0038A8]" />
              <div className="h-full w-[3px] rounded-full bg-[#CE1126]" />
              <div className="h-full w-[3px] rounded-full bg-[#FCD116]" />
            </div>
            <h1
              className="text-base font-semibold tracking-tight"
              style={{ color: "var(--color-text-primary)" }}
            >
              Paper Trail PH
            </h1>
          </div>
          <span
            className="hidden text-xs lg:block"
            style={{ color: "var(--color-text-muted)" }}
          >
            Follow the paper trail
          </span>
        </div>

        {/* Search */}
        <div className="mx-4 flex max-w-lg flex-1 items-center justify-center lg:mx-8">
          <div className="w-full">
            <SearchBar onSelect={onSearchSelect} />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1">
          <button
            onClick={onFilterToggle}
            className={clsx(
              "btn-ghost relative",
              showFilters && "!bg-[var(--btn-ghost-active-bg)]"
            )}
            style={showFilters ? { color: "var(--color-text-primary)" } : undefined}
            title="Toggle filters"
          >
            <Faders size={18} weight="bold" />
          </button>
          <button
            onClick={onChatToggle}
            className={clsx(
              "btn-ghost relative",
              showChat && "!bg-[var(--btn-ghost-active-bg)]"
            )}
            style={showChat ? { color: "var(--color-text-primary)" } : undefined}
            title="Ask about the data"
          >
            <ChatCircle size={18} weight="bold" />
          </button>
          <button
            onClick={toggleTheme}
            className="btn-ghost relative"
            title={theme === "light" ? "Switch to dark mode" : "Switch to light mode"}
          >
            {theme === "light" ? (
              <Moon size={18} weight="bold" />
            ) : (
              <Sun size={18} weight="bold" />
            )}
          </button>
        </div>
      </div>
    </header>
  );
}
