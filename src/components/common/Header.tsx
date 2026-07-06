"use client";

import { ArrowSquareOut } from "@phosphor-icons/react";
import ThemeToggle from "@/components/common/ThemeToggle";
import LogoMark from "@/components/common/LogoMark";

const NAV = [
  { href: "#story", label: "The record" },
  { href: "#explore", label: "Explore" },
  { href: "#analysis", label: "Analysis" },
  { href: "#methodology", label: "Methodology" },
];

export default function Header() {
  return (
    <header
      className="sticky top-0 z-50 border-b border-hairline"
      style={{ backgroundColor: "color-mix(in srgb, var(--page) 88%, transparent)", backdropFilter: "blur(8px)" }}
    >
      <div className="mx-auto flex max-w-content flex-wrap items-center gap-x-6 gap-y-2 px-4 py-2.5 md:px-6">
        <a href="#main" className="flex items-center gap-2">
          <LogoMark size={20} className="text-accent" />
          <span className="font-display text-[17px] font-bold tracking-tight text-text-primary">Paper Trail PH</span>
          <span className="hidden text-xs text-text-muted sm:inline">· DPWH flood-control records</span>
        </a>
        <nav className="ml-auto flex flex-wrap items-center justify-end gap-1 text-sm" aria-label="Primary">
          {NAV.map((n) => (
            <a key={n.href} href={n.href} className="rounded-md px-1.5 py-1.5 text-[13px] text-text-secondary hover:bg-surface-2 hover:text-text-primary sm:px-2.5 sm:text-sm">
              {n.label}
            </a>
          ))}
          <a
            href="https://huggingface.co/datasets/bettergovph/dpwh-transparency-data"
            target="_blank"
            rel="noopener noreferrer"
            className="chip ml-1 hidden md:inline-flex hover:border-accent"
          >
            Source: DPWH via BetterGov.PH · CC0 <ArrowSquareOut size={11} />
          </a>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}
