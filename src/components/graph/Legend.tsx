"use client";

import { TIERS, STATUS } from "@/lib/tiers";
import type { ColorBy } from "@/components/graph/GraphView";

interface Props {
  colorBy: ColorBy;
  setColorBy: (v: ColorBy) => void;
  showDerived: boolean;
  setShowDerived: (v: boolean) => void;
  showEntities: boolean;
  setShowEntities: (v: boolean) => void;
}

export default function Legend({ colorBy, setColorBy, showDerived, setShowDerived, showEntities, setShowEntities }: Props) {
  return (
    <div className="panel max-h-[min(60vh,420px)] w-[248px] overflow-y-auto p-3 text-xs custom-scrollbar" style={{ backgroundColor: "color-mix(in srgb, var(--surface) 94%, transparent)" }}>
      <p className="eyebrow mb-1.5">Links</p>
      <ul className="mb-3 space-y-1.5">
        <li className="flex items-start gap-2">
          <svg width="22" height="10" className="mt-0.5 shrink-0"><line x1="1" y1="5" x2="21" y2="5" stroke="var(--tier-recorded)" strokeWidth="2" /></svg>
          <span className="text-text-secondary">{TIERS.recorded.label}</span>
        </li>
        <li className="flex items-start gap-2">
          <svg width="22" height="10" className="mt-0.5 shrink-0"><path d="M1 8 Q11 -2 21 8" stroke="var(--tier-derived)" strokeWidth="1.5" fill="none" opacity="0.7" /></svg>
          <span className="text-text-secondary">{TIERS.derived.label}</span>
        </li>
      </ul>

      <p className="eyebrow mb-1.5">Nodes</p>
      <ul className="mb-2 space-y-1.5">
        {(["normal", "action", "alleged", "news", "entity"] as const).map((k) => {
          const s = STATUS[k];
          const isEntity = k === "entity";
          return (
            <li key={k} className="flex items-start gap-2">
              <svg width="12" height="12" className="mt-0.5 shrink-0">
                {isEntity
                  ? <rect x="2" y="2" width="8" height="8" fill={`var(${s.cssVar})`} />
                  : <circle cx="6" cy="6" r="4.5" fill={`var(${s.cssVar})`} />}
              </svg>
              <span className="text-text-secondary">{s.label}</span>
            </li>
          );
        })}
      </ul>
      <p className="mb-3 text-[11px] text-text-muted">Node size = recorded flood-control value.</p>

      <p className="eyebrow mb-1.5">View</p>
      <div className="mb-2 inline-flex rounded-md border border-hairline p-0.5" role="group" aria-label="Colour nodes by">
        <button onClick={() => setColorBy("status")} aria-pressed={colorBy === "status"} className={`rounded px-2 py-1 ${colorBy === "status" ? "bg-accent text-white" : "text-text-secondary"}`}>Status</button>
        <button onClick={() => setColorBy("community")} aria-pressed={colorBy === "community"} className={`rounded px-2 py-1 ${colorBy === "community" ? "bg-accent text-white" : "text-text-secondary"}`}>Community</button>
      </div>
      {colorBy === "community" && (
        <p className="mb-2 text-[11px] text-text-muted">Colours = co-award communities (color-blind-safe set), computed by Louvain.</p>
      )}
      <label className="mb-1.5 flex items-center gap-2 text-text-secondary">
        <input type="checkbox" checked={showDerived} onChange={(e) => setShowDerived(e.target.checked)} />
        Show inferred links
      </label>
      <label className="flex items-center gap-2 text-text-secondary">
        <input type="checkbox" checked={showEntities} onChange={(e) => setShowEntities(e.target.checked)} />
        Show district offices
      </label>
    </div>
  );
}
