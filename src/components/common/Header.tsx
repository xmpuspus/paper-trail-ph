"use client";

import { Drop, ArrowSquareOut } from "@phosphor-icons/react";
import ThemeToggle from "@/components/common/ThemeToggle";

const NAV = [
  { href: "#story", label: "The scandal" },
  { href: "#explore", label: "Explore" },
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
          <Drop size={20} weight="fill" className="text-accent" />
          <span className="font-display text-[17px] font-bold tracking-tight text-text-primary">Paper Trail PH</span>
          <span className="hidden text-xs text-text-muted sm:inline">· the flood-control money, mapped</span>
        </a>
        <nav className="ml-auto flex items-center gap-1 text-sm" aria-label="Primary">
          {NAV.map((n) => (
            <a key={n.href} href={n.href} className="rounded-md px-2.5 py-1.5 text-text-secondary hover:bg-surface-2 hover:text-text-primary">
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
