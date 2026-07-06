"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import dynamic from "next/dynamic";
import { Graph, Table, ArrowsOut, CircleNotch } from "@phosphor-icons/react";
import type { GraphData, Entity, Overlay, InNews, Stats } from "@/lib/types";
import { fetchEntities, fetchMainGraph } from "@/lib/client-data";
import { peso } from "@/lib/format";
import type { ColorBy } from "@/components/graph/GraphView";
import Legend from "@/components/graph/Legend";
import GraphTableFallback from "@/components/graph/GraphTableFallback";
import SearchBox from "@/components/search/SearchBox";
import EntityDetail from "@/components/graph/EntityDetail";

const GraphView = dynamic(() => import("@/components/graph/GraphView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center bg-page">
      <CircleNotch size={28} className="animate-spin text-text-muted" />
    </div>
  ),
});

interface Props {
  scandalGraph: GraphData;
  overlay: Overlay;
  inNews: InNews;
  stats: Stats;
}

const QUICK = ["Topnotch", "Sunwest", "Legacy", "St. Gerrard", "MG Samidan", "Wawao"];

export default function Explorer({ scandalGraph, overlay, inNews, stats }: Props) {
  const [entities, setEntities] = useState<Entity[] | null>(null);
  const [entityMap, setEntityMap] = useState<Map<string, Entity>>(new Map());
  const [selectedKey, setSelectedKey] = useState<string | null>(null);
  const [colorBy, setColorBy] = useState<ColorBy>("status");
  const [showDerived, setShowDerived] = useState(false);
  const [showEntities, setShowEntities] = useState(true);
  const [view, setView] = useState<"graph" | "table">("graph");
  const [graph, setGraph] = useState<GraphData>(scandalGraph);
  const [full, setFull] = useState(false);
  const [loadingFull, setLoadingFull] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Load the searchable index once; used by search + the detail lookup.
  useEffect(() => {
    let live = true;
    fetchEntities()
      .then((e) => {
        if (!live) return;
        setEntities(e);
        setEntityMap(new Map(e.map((x) => [x.key, x])));
      })
      .catch(() => {});
    return () => { live = false; };
  }, []);

  // On small screens the WebGL graph degrades to the searchable table.
  useEffect(() => {
    const mq = window.matchMedia("(max-width: 820px)");
    const apply = () => { setIsMobile(mq.matches); if (mq.matches) setView("table"); };
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const displayGraph = useMemo(() => {
    if (showEntities) return graph;
    return { nodes: graph.nodes.filter((n) => n.type !== "ProcuringEntity"), edges: graph.edges.filter((e) => e.type !== "AWARDED_TO") };
  }, [graph, showEntities]);

  const selectedEntity = selectedKey ? entityMap.get(selectedKey) ?? null : null;

  const onSelect = useCallback((key: string | null) => setSelectedKey(key), []);

  const loadFull = useCallback(async () => {
    if (full) { setGraph(scandalGraph); setFull(false); return; }
    setLoadingFull(true);
    try {
      const g = await fetchMainGraph();
      setGraph(g);
      setFull(true);
    } finally {
      setLoadingFull(false);
    }
  }, [full, scandalGraph]);

  return (
    <div id="explore" className="scroll-mt-20">
      {/* Search-first */}
      <div className="mb-4">
        <SearchBox onSelect={(k) => setSelectedKey(k)} entities={entities ?? undefined} overlay={overlay} />
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-text-muted">Jump to:</span>
          {QUICK.map((q) => {
            const match = entities?.find((e) => e.type === "Contractor" && e.label.toUpperCase().includes(q.toUpperCase()));
            return (
              <button
                key={q}
                disabled={!match}
                onClick={() => match && setSelectedKey(match.key)}
                className="chip disabled:opacity-40 hover:border-accent"
              >
                {q}
              </button>
            );
          })}
        </div>
      </div>

      {/* Toolbar */}
      <div className="mb-3 flex flex-wrap items-center gap-2">
        {!isMobile && (
          <div className="inline-flex rounded-lg border border-hairline p-0.5" role="group" aria-label="Graph or table view">
            <button onClick={() => setView("graph")} aria-pressed={view === "graph"} className={`btn text-[13px] ${view === "graph" ? "btn-primary" : "btn-ghost border-0"}`}>
              <Graph size={15} /> Graph
            </button>
            <button onClick={() => setView("table")} aria-pressed={view === "table"} className={`btn text-[13px] ${view === "table" ? "btn-primary" : "btn-ghost border-0"}`}>
              <Table size={15} /> Table
            </button>
          </div>
        )}
        <button onClick={loadFull} className="btn btn-ghost text-[13px]" aria-pressed={full}>
          {loadingFull ? <CircleNotch size={15} className="animate-spin" /> : <ArrowsOut size={15} />}
          {full ? "Show the named firms" : `Show full flood-control network (${stats.graph_main_nodes.toLocaleString()} nodes)`}
        </button>
        <span className="ml-auto text-xs text-text-muted tabular">
          {displayGraph.nodes.length.toLocaleString()} nodes · {displayGraph.edges.length.toLocaleString()} links
        </span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[1fr_380px]">
        {/* Graph / table */}
        <div className="relative h-[560px] min-w-0 overflow-hidden rounded-xl border border-hairline bg-page md:h-[640px]">
          {view === "graph" && !isMobile ? (
            <>
              <GraphView
                data={displayGraph}
                colorBy={colorBy}
                showDerived={showDerived}
                overlay={overlay}
                inNews={inNews}
                selected={selectedKey}
                onSelect={onSelect}
              />
              <div className="absolute bottom-3 left-3 max-w-[280px]">
                <Legend
                  colorBy={colorBy}
                  setColorBy={setColorBy}
                  showDerived={showDerived}
                  setShowDerived={setShowDerived}
                  showEntities={showEntities}
                  setShowEntities={setShowEntities}
                />
              </div>
            </>
          ) : (
            <GraphTableFallback data={displayGraph} onSelect={onSelect} />
          )}
        </div>

        {/* Right sidebar: detail or top firms */}
        <div className="h-[560px] min-w-0 md:h-[640px]">
          {selectedEntity ? (
            <EntityDetail
              entity={selectedEntity}
              overlay={overlay}
              inNews={inNews}
              onClose={() => setSelectedKey(null)}
              onSelectRelated={(k) => setSelectedKey(k)}
            />
          ) : (
            <TopFirms stats={stats} onSelect={setSelectedKey} loaded={!!entities} />
          )}
        </div>
      </div>
    </div>
  );
}

function TopFirms({ stats, onSelect, loaded }: { stats: Stats; onSelect: (k: string) => void; loaded: boolean }) {
  return (
    <div className="flex h-full flex-col overflow-hidden panel">
      <div className="border-b border-hairline p-4">
        <p className="eyebrow">Highest recorded flood-control value</p>
        <p className="mt-1 text-xs text-text-muted">Sum of contract budgets where the firm is sole or joint awardee. Select a firm to see its record.</p>
      </div>
      <ol className="custom-scrollbar flex-1 overflow-y-auto p-2">
        {stats.top_flood_control_firms.slice(0, 20).map((f, i) => (
          <li key={f.key}>
            <button
              onClick={() => loaded && onSelect(f.key)}
              disabled={!loaded}
              className="flex w-full items-baseline justify-between gap-3 rounded-lg px-3 py-2 text-left hover:bg-surface-2 disabled:opacity-50"
            >
              <span className="flex min-w-0 items-baseline gap-2">
                <span className="tabular w-5 shrink-0 text-xs text-text-muted">{i + 1}</span>
                <span className="min-w-0">
                  <span className="block truncate text-sm text-text-primary">{f.name}</span>
                  {f.revoked && <span className="text-[11px] text-signal">license revoked on record</span>}
                </span>
              </span>
              <span className="tabular shrink-0 text-sm font-semibold text-text-primary">{peso(f.fc_value)}</span>
            </button>
          </li>
        ))}
      </ol>
    </div>
  );
}
