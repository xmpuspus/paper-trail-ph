"use client";

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { MagnifyingGlass, CircleNotch } from "@phosphor-icons/react";
import type { Entity, Overlay } from "@/lib/types";
import { fetchEntities } from "@/lib/client-data";
import { buildSearchIndex, searchEntities, type SearchResult } from "@/lib/search";
import { peso } from "@/lib/format";

interface Props {
  onSelect: (key: string) => void;
  entities?: Entity[];
  overlay?: Overlay | null;
  autoFocus?: boolean;
}

export default function SearchBox({ onSelect, entities: provided, overlay, autoFocus }: Props) {
  const [entities, setEntities] = useState<Entity[] | null>(provided ?? null);
  const [error, setError] = useState(false);
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [active, setActive] = useState(0);
  const listId = "search-results";

  useEffect(() => { if (provided) setEntities(provided); }, [provided]);

  useEffect(() => {
    if (provided || entities) return;
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const load = () => {
    setError(false);
    fetchEntities().then(setEntities).catch(() => setError(true));
  };

  useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 150);
    return () => clearTimeout(t);
  }, [q]);

  // Firms + district offices, folded with the sourced overlay so owner names,
  // the persons named in reporting, and former company names are all searchable.
  const index = useMemo(() => buildSearchIndex(entities ?? [], overlay ?? null), [entities, overlay]);

  const results = useMemo(() => (debounced ? searchEntities(index, debounced) : []), [index, debounced]);
  const firstSimilar = results.findIndex((r) => r.similar);

  useEffect(() => setActive(0), [debounced]);

  const choose = (r: SearchResult) => { onSelect(r.entity.key); setQ(""); setDebounced(""); };

  const onKeyDown = (ev: React.KeyboardEvent) => {
    if (!results.length) return;
    if (ev.key === "ArrowDown") { ev.preventDefault(); setActive((a) => Math.min(a + 1, results.length - 1)); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); setActive((a) => Math.max(a - 1, 0)); }
    else if (ev.key === "Enter") { ev.preventDefault(); choose(results[active]); }
  };

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlass size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-text-muted" />
        <input
          type="text"
          value={q}
          autoFocus={autoFocus}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder="Search firms, owners, district offices, and former names…"
          aria-label="Search firms, owners, district offices, and former names"
          role="combobox"
          aria-expanded={results.length > 0}
          aria-controls={listId}
          aria-activedescendant={results.length ? `opt-${active}` : undefined}
          className="search-input pl-10"
          disabled={!entities && !error}
        />
        {!entities && !error && <CircleNotch size={16} className="absolute right-3.5 top-1/2 -translate-y-1/2 animate-spin text-text-muted" />}
      </div>

      {error && (
        <p className="mt-1.5 text-xs text-alert">
          Couldn&apos;t load the index. <button onClick={load} className="link-source">Retry</button>
        </p>
      )}

      {debounced && (
        <ul id={listId} role="listbox" className="panel custom-scrollbar absolute z-30 mt-1.5 max-h-[340px] w-full overflow-y-auto py-1">
          {results.length === 0 ? (
            <li className="px-3 py-2 text-sm text-text-muted">No firm, office, or name matches &quot;{debounced}&quot;.</li>
          ) : (
            results.map((r, i) => (
              <Fragment key={r.entity.id}>
                {i === firstSimilar && (
                  <li role="presentation" className="px-3 pb-1 pt-2 text-[11px] uppercase tracking-wide text-text-muted">
                    Similar
                  </li>
                )}
                <li
                  id={`opt-${i}`}
                  role="option"
                  aria-selected={i === active}
                  onMouseEnter={() => setActive(i)}
                  onClick={() => choose(r)}
                  className={`flex cursor-pointer items-baseline gap-3 px-3 py-2 ${i === active ? "bg-surface-2" : ""}`}
                >
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm text-text-primary">{r.entity.label}</span>
                    <span className="block truncate text-[11px] text-text-muted">
                      {r.entity.type === "Contractor" ? "Contractor" : r.entity.type === "Person" ? "Person on the record" : "District office"}
                      {r.reason?.kind === "name" && <span className="ml-1.5">· matches {r.reason.text}</span>}
                      {r.reason?.kind === "former" && <span className="ml-1.5">· formerly {r.reason.text}</span>}
                      {r.entity.revoked && <span className="ml-1.5 text-signal">· license revoked on record</span>}
                    </span>
                  </span>
                  {r.entity.type !== "Person" && (
                    <span className="tabular shrink-0 text-sm text-text-secondary">{peso(r.entity.fc_value)}</span>
                  )}
                </li>
              </Fragment>
            ))
          )}
        </ul>
      )}

      {!debounced && (
        <p className="mt-1.5 text-xs text-text-muted">Try: Topnotch, Sunwest, Legacy, or a district office.</p>
      )}
    </div>
  );
}
