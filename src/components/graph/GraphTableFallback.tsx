"use client";

import { useMemo, useState } from "react";
import type { GraphData, GraphNode } from "@/lib/types";
import { peso, num } from "@/lib/format";

type SortKey = "label" | "fc_value" | "fc_contracts" | "community";

export default function GraphTableFallback({ data, onSelect }: { data: GraphData; onSelect: (key: string) => void }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("fc_value");
  const [dir, setDir] = useState<"asc" | "desc">("desc");

  const rows = useMemo(() => {
    const needle = q.trim().toUpperCase();
    let r = data.nodes.filter((n) => !needle || n.label.toUpperCase().includes(needle));
    r = [...r].sort((a, b) => {
      const av = valueOf(a, sort);
      const bv = valueOf(b, sort);
      const cmp = typeof av === "string" ? av.localeCompare(bv as string) : (av as number) - (bv as number);
      return dir === "asc" ? cmp : -cmp;
    });
    return r;
  }, [data, q, sort, dir]);

  const shown = rows.slice(0, 200);
  const toggle = (k: SortKey) => {
    if (sort === k) setDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSort(k); setDir(k === "label" ? "asc" : "desc"); }
  };
  const ariaSort = (k: SortKey) => (sort === k ? (dir === "asc" ? "ascending" : "descending") : "none");

  return (
    <div className="flex h-full flex-col p-3">
      <input
        type="text"
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="Filter by name…"
        aria-label="Filter the graph table by name"
        className="search-input mb-2"
      />
      <div className="custom-scrollbar flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <caption className="sr-only">Accessible table view of the graph: contractors and district offices with their recorded flood-control value, contract count, and co-award community.</caption>
          <thead className="sticky top-0 bg-surface">
            <tr className="border-b border-hairline text-left text-[11px] uppercase tracking-wide text-text-muted">
              <Th label="Name" onClick={() => toggle("label")} aria={ariaSort("label")} />
              <Th label="Type" />
              <Th label="Flood-control value" right onClick={() => toggle("fc_value")} aria={ariaSort("fc_value")} />
              <Th label="Contracts" right onClick={() => toggle("fc_contracts")} aria={ariaSort("fc_contracts")} />
              <Th label="Community" right onClick={() => toggle("community")} aria={ariaSort("community")} />
            </tr>
          </thead>
          <tbody>
            {shown.map((n) => (
              <tr key={n.id} className="border-b border-hairline/60 hover:bg-surface-2">
                <td className="py-1.5 pr-2">
                  <button onClick={() => onSelect(n.key)} className="text-left text-text-primary hover:text-accent">
                    {n.label}
                    {n.revoked && <span className="ml-2 text-[11px] text-signal">revoked</span>}
                  </button>
                </td>
                <td className="py-1.5 pr-2 text-text-muted">{n.type === "Contractor" ? "Contractor" : "District office"}</td>
                <td className="tabular py-1.5 pr-2 text-right text-text-secondary">{peso(n.fc_value)}</td>
                <td className="tabular py-1.5 pr-2 text-right text-text-secondary">{num(n.fc_contracts)}</td>
                <td className="tabular py-1.5 text-right text-text-muted">{n.community ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length > 200 && (
          <p className="py-2 text-center text-xs text-text-muted">Showing top 200 of {num(rows.length)} nodes. Filter to narrow.</p>
        )}
      </div>
    </div>
  );
}

function valueOf(n: GraphNode, k: SortKey): number | string {
  if (k === "label") return n.label;
  if (k === "fc_value") return n.fc_value ?? 0;
  if (k === "fc_contracts") return n.fc_contracts ?? 0;
  return n.community ?? -1;
}

function Th({ label, right, onClick, aria }: { label: string; right?: boolean; onClick?: () => void; aria?: string }) {
  return (
    <th aria-sort={aria as never} className={`py-2 ${right ? "pr-2 text-right" : "pr-2"}`}>
      {onClick ? (
        <button onClick={onClick} className="uppercase hover:text-text-secondary">{label}</button>
      ) : (
        label
      )}
    </th>
  );
}
