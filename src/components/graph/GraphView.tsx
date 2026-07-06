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
  showPredicted?: boolean;
  overlay: Overlay | null;
  inNews: InNews | null;
  selected: string | null;
  onSelect: (key: string | null) => void;
}

function resolveColors(theme: string) {
  const light = theme !== "dark";
  return {
    status: {
      alleged: cssColor("--alert", "#ee6b52"),
      action: cssColor("--signal", "#e8a33d"),
      news: cssColor("--water", "#38b2c4"),
      entity: cssColor("--node-entity", "#4a90f0"),
      person: cssColor("--node-person", "#9d7bc4"),
      normal: cssColor("--node-contractor", "#8aa0bb"),
    } as Record<string, string>,
    cat: Array.from({ length: 8 }, (_, i) => cssColor(`--cat-${i + 1}`, "#888")),
    catOther: cssColor("--cat-other", "#888"),
    // Faint edges so the nodes carry the picture. More opaque in light mode,
    // where a low alpha washes out against the pale surface.
    tierRecorded: cssColor("--tier-recorded", "#9db2cc") + (light ? "8c" : "4d"),
    tierDerived: cssColor("--tier-derived", "#38b2c4") + (light ? "99" : "66"),
    tierPredicted: cssColor("--tier-predicted", "#9d7bc4") + (light ? "8c" : "59"),
    // The connected edges when a node is focused: strong enough to read.
    focusEdge: cssColor("--tier-recorded", "#9db2cc") + "e0",
    // Dimmed non-neighbour nodes: a visible grey in light mode; a faded alpha
    // in dark mode (a low alpha turns white on a pale surface).
    dimNode: light ? "#b6bdc6" : null,
    label: cssColor("--graph-label", "#a2b4ca"),
  };
}

function GraphLoader({ data, colorBy, showDerived, showPredicted = false, overlay, inNews, selected, onSelect }: LoaderProps) {
  const loadGraph = useLoadGraph();
  const registerEvents = useRegisterEvents();
  const sigma = useSigma();
  const { theme } = useTheme();
  const [hovered, setHovered] = useState<string | null>(null);
  const nodeById = useRef<Map<string, GraphNode>>(new Map());
  const keyToId = useRef<Map<string, string>>(new Map());

  // Build + lay out the graph (rebuilds only when the dataset changes).
  useEffect(() => {
    const C = resolveColors(theme);
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
      const predicted = e.tier === "predicted";
      // A concise label, shown only when an endpoint is focused (see edgeReducer).
      // The full sentence lives in the entity detail; on-canvas it stays short.
      const elabel =
        e.type === "CO_AWARDED_WITH"
          ? "joint venture"
          : e.type === "CO_LOCATED"
            ? `${e.weight} shared offices`
            : e.type === "PERSON_LINK"
              ? "person on record"
              : e.type === "PREDICTED_TIE"
                ? "predicted (statistical)"
                : `${e.weight} contract${e.weight === 1 ? "" : "s"}`;
      graph.addEdgeWithKey(e.id, e.source, e.target, {
        size: predicted ? 0.4 : derived ? 0.45 : Math.max(0.35, Math.min(1.5, Math.log10((e.weight || 1) + 1) * 0.9)),
        color: predicted ? C.tierPredicted : derived ? C.tierDerived : C.tierRecorded,
        type: derived || predicted ? "curved" : "straight",
        tier: e.tier,
        elabel,
        w: e.weight || 1,
        hidden: (derived && !showDerived) || (predicted && !showPredicted),
      });
    });

    // Organic force-directed layout (no community pre-packing, which produced
    // tight circular clumps). Random seed positions were set on each node.
    loadGraph(graph);
    const big = graph.order > 900;
    forceAtlas2.assign(graph, {
      iterations: big ? 200 : 420,
      settings: {
        gravity: big ? 0.5 : 0.28,
        scalingRatio: big ? 16 : 34,
        linLogMode: true,
        adjustSizes: true,
        slowDown: 5,
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
    const C = resolveColors(theme);
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
      graph.setEdgeAttribute(
        id,
        "color",
        tier === "predicted" ? C.tierPredicted : tier === "derived" ? C.tierDerived : C.tierRecorded,
      );
    });
    sigma.refresh();
  }, [colorBy, theme, sigma]);

  // Toggle inferred (derived) and predicted (statistical) edges.
  useEffect(() => {
    const graph = sigma.getGraph();
    graph.forEachEdge((id) => {
      const tier = graph.getEdgeAttribute(id, "tier") as string;
      if (tier === "derived") graph.setEdgeAttribute(id, "hidden", !showDerived);
      if (tier === "predicted") graph.setEdgeAttribute(id, "hidden", !showPredicted);
    });
    sigma.refresh();
  }, [showDerived, showPredicted, sigma]);

  // Selection + hover highlight. Explorer tracks canonical keys; resolve to ids.
  useEffect(() => {
    const graph = sigma.getGraph();
    const C = resolveColors(theme);
    const selectedId = selected ? keyToId.current.get(selected) ?? null : null;
    const focus = hovered || selectedId;
    sigma.setSetting("nodeReducer", (id, d) => {
      const res = { ...d };
      if (selectedId && id === selectedId) { res.highlighted = true; res.zIndex = 3; }
      if (focus) {
        if (id === focus) { res.zIndex = 3; res.highlighted = true; }
        else if (graph.areNeighbors(id, focus)) { res.zIndex = 2; }
        else { res.color = C.dimNode ?? ((d.color as string) + "22"); res.label = ""; res.zIndex = 0; }
      }
      return res;
    });
    sigma.setSetting("edgeReducer", (id, d) => {
      if (!focus) return d;
      const [s, t] = graph.extremities(id);
      if (s === focus || t === focus) {
        // On focus, width scales with the number of contracts (sqrt, clamped),
        // so a 50-contract award reads thicker than a 3-contract one.
        const w = (d.w as number) || 1;
        const size = Math.max(1, Math.min(7, Math.sqrt(w) * 0.85));
        return { ...d, color: C.focusEdge, zIndex: 2, size, label: d.elabel as string };
      }
      return { ...d, hidden: true };
    });
    sigma.refresh({ skipIndexation: true });
  }, [hovered, selected, theme, sigma]);

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
  showPredicted?: boolean;
  overlay: Overlay | null;
  inNews: InNews | null;
  selected: string | null;
  onSelect: (key: string | null) => void;
}

export default function GraphView({ data, colorBy, showDerived, showPredicted, overlay, inNews, selected, onSelect }: GraphViewProps) {
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
        // Edge labels are opt-in per edge: only the focused node's edges carry a
        // label (set in the edgeReducer), so the dense graph stays readable.
        renderEdgeLabels: true,
        edgeLabelFont: "var(--font-body), system-ui, sans-serif",
        edgeLabelSize: 11,
        edgeLabelWeight: "500",
        edgeLabelColor: { color: labelColor },
        zIndex: true,
      }}
    >
      <GraphLoader
        data={data}
        colorBy={colorBy}
        showDerived={showDerived}
        showPredicted={showPredicted}
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
