"use client";

import { useState } from "react";
import { CaretDown, ListBullets } from "@phosphor-icons/react";
import { TIERS, STATUS } from "@/lib/tiers";
import type { ColorBy } from "@/components/graph/GraphView";

interface Props {
  colorBy: ColorBy;
  setColorBy: (v: ColorBy) => void;
  showDerived: boolean;
  setShowDerived: (v: boolean) => void;
  showPredicted: boolean;
  setShowPredicted: (v: boolean) => void;
  showEntities: boolean;
  setShowEntities: (v: boolean) => void;
}

export default function Legend({ colorBy, setColorBy, showDerived, setShowDerived, showPredicted, setShowPredicted, showEntities, setShowEntities }: Props) {
  const [open, setOpen] = useState(false);

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="panel inline-flex items-center gap-2 px-3 py-2 text-xs font-medium text-text-secondary shadow-sm hover:text-text-primary"
        aria-expanded={false}
      >
        <ListBullets size={14} /> Legend &amp; filters
      </button>
    );
  }

  return (
    <div className="panel w-[224px] p-3 text-xs shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <span className="font-semibold text-text-primary">Legend &amp; filters</span>
        <button onClick={() => setOpen(false)} className="text-text-muted hover:text-text-primary" aria-label="Collapse legend">
          <CaretDown size={14} />
        </button>
      </div>

      <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-text-muted">Links</p>
      <ul className="mb-2.5 space-y-1">
        <li className="flex items-center gap-2">
          <svg width="20" height="8" className="shrink-0"><line x1="1" y1="4" x2="19" y2="4" stroke="var(--tier-recorded)" strokeWidth="2" /></svg>
          <span className="text-text-secondary">{TIERS.recorded.label}</span>
        </li>
        <li className="flex items-center gap-2">
          <svg width="20" height="8" className="shrink-0"><path d="M1 7 Q10 -2 19 7" stroke="var(--tier-derived)" strokeWidth="1.5" fill="none" /></svg>
          <span className="text-text-secondary">{TIERS.derived.label}</span>
        </li>
        <li className="flex items-center gap-2">
          <svg width="20" height="8" className="shrink-0"><path d="M1 7 Q10 -2 19 7" stroke="var(--tier-predicted)" strokeWidth="1.2" strokeDasharray="2 2" fill="none" opacity="0.8" /></svg>
          <span className="text-text-secondary">{TIERS.predicted.label}</span>
        </li>
      </ul>

      <p className="mb-1 text-[11px] font-medium uppercase tracking-wide text-text-muted">Nodes</p>
      <ul className="mb-1.5 space-y-1">
        {(["normal", "action", "alleged", "news", "entity", "person"] as const).map((k) => {
          const s = STATUS[k];
          const isEntity = k === "entity";
          return (
            <li key={k} className="flex items-center gap-2">
              <svg width="11" height="11" className="shrink-0">
                {isEntity ? <rect x="1.5" y="1.5" width="8" height="8" fill={`var(${s.cssVar})`} /> : <circle cx="5.5" cy="5.5" r={k === "person" ? 3 : 4.5} fill={`var(${s.cssVar})`} />}
              </svg>
              <span className="text-text-secondary">{s.label}</span>
            </li>
          );
        })}
      </ul>
      <p className="mb-2.5 text-[11px] text-text-muted">Node size = recorded flood-control value.</p>

      <div className="mb-2 inline-flex rounded-md border border-hairline p-0.5" role="group" aria-label="Colour nodes by">
        <button onClick={() => setColorBy("status")} aria-pressed={colorBy === "status"} className={`rounded px-2 py-0.5 ${colorBy === "status" ? "bg-accent text-white" : "text-text-secondary"}`}>Status</button>
        <button onClick={() => setColorBy("community")} aria-pressed={colorBy === "community"} className={`rounded px-2 py-0.5 ${colorBy === "community" ? "bg-accent text-white" : "text-text-secondary"}`}>Community</button>
      </div>
      <label className="mb-1 flex items-center gap-2 text-text-secondary">
        <input type="checkbox" checked={showDerived} onChange={(e) => setShowDerived(e.target.checked)} /> Show inferred links
      </label>
      <label className="mb-1 flex items-center gap-2 text-text-secondary">
        <input type="checkbox" checked={showPredicted} onChange={(e) => setShowPredicted(e.target.checked)} /> Show predicted ties (unverified)
      </label>
      <label className="flex items-center gap-2 text-text-secondary">
        <input type="checkbox" checked={showEntities} onChange={(e) => setShowEntities(e.target.checked)} /> Show district offices
      </label>
    </div>
  );
}
