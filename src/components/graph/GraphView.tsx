"use client";

import { useEffect, useRef, useState } from "react";
import { SigmaContainer, useLoadGraph, useRegisterEvents, useSigma } from "@react-sigma/core";
import "@react-sigma/core/lib/react-sigma.min.css";
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { NodeCircleProgram } from "sigma/rendering";
import { NodeSquareProgram } from "@sigma/node-square";
import EdgeCurveProgram from "@sigma/edge-curve";
import type { GraphData, GraphNode } from "@/lib/types";
import { nodeStatus, nodeRadius, communityVar, cssColor, STATUS } from "@/lib/tiers";
import type { Overlay, InNews } from "@/lib/types";
import { peso } from "@/lib/format";
import { useTheme } from "@/components/common/ThemeProvider";

export type ColorBy = "status" | "community";

interface LoaderProps {
  data: GraphData;
  colorBy: ColorBy;
  showDerived: boolean;
  overlay: Overlay | null;
  inNews: InNews | null;
  selected: string | null;
  onSelect: (key: string | null) => void;
}

function resolveColors() {
  return {
    status: {
      alleged: cssColor("--alert", "#ee6b52"),
      action: cssColor("--signal", "#e8a33d"),
      news: cssColor("--water", "#38b2c4"),
      entity: cssColor("--node-entity", "#4a90f0"),
      normal: cssColor("--node-contractor", "#8aa0bb"),
    } as Record<string, string>,
    cat: Array.from({ length: 8 }, (_, i) => cssColor(`--cat-${i + 1}`, "#888")),
    catOther: cssColor("--cat-other", "#888"),
    tierRecorded: cssColor("--tier-recorded", "#9db2cc"),
    tierDerived: cssColor("--tier-derived", "#38b2c4"),
    label: cssColor("--graph-label", "#a2b4ca"),
  };
}

function GraphLoader({ data, colorBy, showDerived, overlay, inNews, selected, onSelect }: LoaderProps) {
  const loadGraph = useLoadGraph();
  const registerEvents = useRegisterEvents();
  const sigma = useSigma();
  const { theme } = useTheme();
  const [hovered, setHovered] = useState<string | null>(null);
  const nodeById = useRef<Map<string, GraphNode>>(new Map());
  const keyToId = useRef<Map<string, string>>(new Map());

  // Build + lay out the graph (rebuilds only when the dataset changes).
  useEffect(() => {
    const C = resolveColors();
    const graph = new Graph({ multi: false });
    nodeById.current = new Map(data.nodes.map((n) => [n.id, n]));
    keyToId.current = new Map(data.nodes.map((n) => [n.key, n.id]));

    data.nodes.forEach((n) => {
      const st = nodeStatus(n, overlay, inNews);
      const fill =
        colorBy === "community" && n.type === "Contractor"
          ? (n.community != null ? C.cat[n.community % 8] : C.catOther)
          : C.status[st];
      if (!graph.hasNode(n.id)) {
        graph.addNode(n.id, {
          label: n.label,
          x: Math.random() * 100,
          y: Math.random() * 100,
          size: nodeRadius(n),
          color: fill,
          type: n.type === "ProcuringEntity" ? "square" : "circle",
          nodeType: n.type,
          community: n.community ?? 0,
          statusKey: st,
          key: n.key,
        });
      }
    });

    data.edges.forEach((e) => {
      if (!graph.hasNode(e.source) || !graph.hasNode(e.target)) return;
      if (graph.hasEdge(e.source, e.target)) return;
      const derived = e.tier === "derived";
      graph.addEdgeWithKey(e.id, e.source, e.target, {
        size: derived ? 0.45 : Math.max(0.35, Math.min(1.5, Math.log10((e.weight || 1) + 1) * 0.9)),
        color: derived ? C.tierDerived : C.tierRecorded,
        type: derived ? "curved" : "straight",
        tier: e.tier,
        hidden: derived && !showDerived,
      });
    });

    // Organic force-directed layout (no community pre-packing, which produced
    // tight circular clumps). Random seed positions were set on each node.
    loadGraph(graph);
    forceAtlas2.assign(graph, {
      iterations: 300,
      settings: {
        gravity: 0.6,
        scalingRatio: 14,
        linLogMode: true,
        adjustSizes: true,
        slowDown: 6,
        barnesHutOptimize: true,
        outboundAttractionDistribution: true,
      },
    });
    sigma.refresh();
    requestAnimationFrame(() => sigma.getCamera().animatedReset({ duration: 0 }));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, loadGraph, sigma]);

  // Recolor on colorBy / theme change without relaying out.
  useEffect(() => {
    const graph = sigma.getGraph();
    if (graph.order === 0) return;
    const C = resolveColors();
    graph.forEachNode((id) => {
      const nt = graph.getNodeAttribute(id, "nodeType") as string;
      const st = graph.getNodeAttribute(id, "statusKey") as string;
      const comm = graph.getNodeAttribute(id, "community") as number;
      const fill =
        colorBy === "community" && nt === "Contractor"
          ? C.cat[comm % 8]
          : C.status[st];
      graph.setNodeAttribute(id, "color", fill);
    });
    graph.forEachEdge((id) => {
      const tier = graph.getEdgeAttribute(id, "tier") as string;
      graph.setEdgeAttribute(id, "color", tier === "derived" ? C.tierDerived : C.tierRecorded);
    });
    sigma.refresh();
  }, [colorBy, theme, sigma]);

  // Toggle inferred (derived) edges.
  useEffect(() => {
    const graph = sigma.getGraph();
    graph.forEachEdge((id) => {
      if ((graph.getEdgeAttribute(id, "tier") as string) === "derived") {
        graph.setEdgeAttribute(id, "hidden", !showDerived);
      }
    });
    sigma.refresh();
  }, [showDerived, sigma]);

  // Selection + hover highlight. Explorer tracks canonical keys; resolve to ids.
  useEffect(() => {
    const graph = sigma.getGraph();
    const selectedId = selected ? keyToId.current.get(selected) ?? null : null;
    const focus = hovered || selectedId;
    sigma.setSetting("nodeReducer", (id, d) => {
      const res = { ...d };
      if (selectedId && id === selectedId) { res.highlighted = true; res.zIndex = 3; }
      if (focus) {
        if (id === focus) { res.zIndex = 3; res.highlighted = true; }
        else if (graph.areNeighbors(id, focus)) { res.zIndex = 2; }
        else { res.color = (d.color as string) + "22"; res.label = ""; res.zIndex = 0; }
      }
      return res;
    });
    sigma.setSetting("edgeReducer", (id, d) => {
      if (!focus) return d;
      const [s, t] = graph.extremities(id);
      if (s === focus || t === focus) return { ...d, zIndex: 2, size: Math.max((d.size as number) || 0.6, 1.6) };
      return { ...d, hidden: true };
    });
    sigma.refresh({ skipIndexation: true });
  }, [hovered, selected, sigma]);

  useEffect(() => {
    registerEvents({
      clickNode: (e) => onSelect(graphKey(sigma, e.node)),
      clickStage: () => onSelect(null),
      enterNode: (e) => { setHovered(e.node); sigma.getContainer().style.cursor = "pointer"; },
      leaveNode: () => { setHovered(null); sigma.getContainer().style.cursor = "default"; },
    });
  }, [registerEvents, onSelect, sigma]);

  return null;
}

function graphKey(sigma: ReturnType<typeof useSigma>, id: string): string {
  try { return sigma.getGraph().getNodeAttribute(id, "key") as string; } catch { return id; }
}

interface GraphViewProps {
  data: GraphData;
  colorBy: ColorBy;
  showDerived: boolean;
  overlay: Overlay | null;
  inNews: InNews | null;
  selected: string | null;
  onSelect: (key: string | null) => void;
}

export default function GraphView({ data, colorBy, showDerived, overlay, inNews, selected, onSelect }: GraphViewProps) {
  const { theme } = useTheme();
  const bg = theme === "dark" ? "#0a1017" : "#eef2f7";
  const labelColor = theme === "dark" ? "#a2b4ca" : "#46586e";

  if (!data.nodes.length) {
    return (
      <div className="flex h-full w-full items-center justify-center text-sm text-text-muted">
        No graph data to show.
      </div>
    );
  }

  return (
    <SigmaContainer
      graph={Graph}
      style={{ height: "100%", width: "100%", background: bg }}
      settings={{
        defaultNodeType: "circle",
        defaultEdgeType: "straight",
        nodeProgramClasses: { circle: NodeCircleProgram, square: NodeSquareProgram },
        edgeProgramClasses: { straight: EdgeCurveProgram, curved: EdgeCurveProgram },
        labelFont: "var(--font-body), system-ui, sans-serif",
        labelSize: 12,
        labelWeight: "600",
        labelColor: { color: labelColor },
        labelDensity: 0.2,
        labelGridCellSize: 220,
        labelRenderedSizeThreshold: 7,
        zIndex: true,
      }}
    >
      <GraphLoader
        data={data}
        colorBy={colorBy}
        showDerived={showDerived}
        overlay={overlay}
        inNews={inNews}
        selected={selected}
        onSelect={onSelect}
      />
    </SigmaContainer>
  );
}

// Small helper exported for the legend + fallback table.
export function nodeSummary(n: GraphNode): string {
  if (n.type === "ProcuringEntity") return `${n.region ?? ""} · ${peso(n.fc_value)} flood control`;
  return `${peso(n.fc_value)} flood control · ${n.fc_contracts ?? 0} contracts`;
}
