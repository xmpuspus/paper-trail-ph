"use client";

import { useEffect, useRef, useState } from "react";
import { SigmaContainer, useLoadGraph, useRegisterEvents, useSigma } from "@react-sigma/core";
import "@react-sigma/core/lib/react-sigma.min.css";
import { MultiGraph } from "graphology";
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import louvain from "graphology-communities-louvain";
import circlepack from "graphology-layout/circlepack";
import { NodeCircleProgram } from "sigma/rendering";
import { NodeSquareProgram } from "@sigma/node-square";
import { createNodeBorderProgram } from "@sigma/node-border";
import { EdgeCurvedArrowProgram, indexParallelEdgesIndex } from "@sigma/edge-curve";
import type { GraphData, NodeType } from "@/types/graph";
import { NODE_COLORS, NODE_SIZES, NODE_SHAPES, EDGE_COLORS, formatCompact } from "@/lib/constants";
import { EDGE_EXPLANATIONS } from "@/components/graph/EdgeDetail";
import { NodeDiamondProgram, NodeTriangleProgram } from "@/lib/node-programs";
import { useTheme } from "@/components/common/ThemeProvider";

const NodeBorderedProgram = createNodeBorderProgram({
  borders: [
    { size: { value: 0.2, mode: "relative" }, color: { attribute: "borderColor", defaultValue: "#fff" } },
    { size: { fill: true }, color: { attribute: "color" } },
  ],
});

function tooltipShapeSvg(shape: string, color: string): string {
  const s = 10;
  switch (shape) {
    case "square":
      return `<svg width="${s}" height="${s}" style="flex-shrink:0"><rect x="1" y="1" width="8" height="8" fill="${color}"/></svg>`;
    case "diamond":
      return `<svg width="${s}" height="${s}" style="flex-shrink:0"><rect x="1.5" y="1.5" width="7" height="7" fill="${color}" transform="rotate(45,5,5)"/></svg>`;
    case "triangle":
      return `<svg width="${s}" height="${s}" style="flex-shrink:0"><polygon points="5,1 9,9 1,9" fill="${color}"/></svg>`;
    case "bordered":
      return `<svg width="${s}" height="${s}" style="flex-shrink:0"><circle cx="5" cy="5" r="4" fill="${color}" stroke="${lightenColor(color, 0.6)}" stroke-width="1.5"/></svg>`;
    default:
      return `<svg width="${s}" height="${s}" style="flex-shrink:0"><circle cx="5" cy="5" r="4" fill="${color}"/></svg>`;
  }
}

function lightenColor(hex: string, amount: number): string {
  const num = parseInt(hex.replace("#", ""), 16);
  const r = Math.min(255, ((num >> 16) & 0xff) + Math.round(255 * amount));
  const g = Math.min(255, ((num >> 8) & 0xff) + Math.round(255 * amount));
  const b = Math.min(255, (num & 0xff) + Math.round(255 * amount));
  return `#${((r << 16) | (g << 8) | b).toString(16).padStart(6, "0")}`;
}

function getKeyProp(nodeType: string, props: Record<string, unknown>): string | null {
  switch (nodeType) {
    case "Contract": {
      const amt = props.amount as number | undefined;
      return amt ? formatCompact(amt) : null;
    }
    case "Politician":
      return (props.position as string) || null;
    case "Contractor":
      return (props.classification as string) || null;
    case "Agency":
      return (props.department as string) || null;
    case "AuditFinding":
      return (props.severity as string) || null;
    case "PoliticalFamily":
      return props.member_count ? `${props.member_count} members` : null;
    case "Municipality":
      return (props.province as string) || null;
    default:
      return null;
  }
}

function edgeSizeFromValue(props: Record<string, unknown>): number {
  const value = (props.bid_amount || props.subcontract_value || props.amount) as number | undefined;
  if (!value || value <= 0) return 0.8;
  // Log scale: P50K → 0.8, P1M → 1.4, P100M → 2.6, P890M → 3.4
  return Math.max(0.6, Math.min(4.0, 0.8 + Math.log10(value / 50_000) * 0.6));
}

// Darker edge colors for light mode — originals wash out on #f0f0f3
const LIGHT_EDGE_OVERRIDES: Record<string, string> = {
  HAS_AGENCY: "#334155",
  BID_ON: "#525252",
  CO_AUTHORED_WITH: "#7c3aed",
  MEMBER_OF: "#4338ca",
  SUBCONTRACTED_TO: "#6d28d9",
  OWNED_BY: "#44403c",
  LOCATED_IN: "#37474F",
  ALLIED_WITH: "#1e3a8a",
};

function edgeColor(type: string, isDark: boolean): string {
  if (!isDark && LIGHT_EDGE_OVERRIDES[type]) return LIGHT_EDGE_OVERRIDES[type];
  return EDGE_COLORS[type] || (isDark ? "#555" : "#64748b");
}

/** Append hex alpha to an existing hex color */
function withAlpha(hex: string, alpha: number): string {
  const a = Math.round(alpha * 255).toString(16).padStart(2, "0");
  return hex.length === 7 ? hex + a : hex.slice(0, 7) + a;
}

interface GraphLoaderProps {
  data: GraphData;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  visibleTypes: Set<NodeType>;
  highlightedNodes?: Set<string>;
}

function GraphLoader({
  data,
  onNodeClick,
  onEdgeClick,
  visibleTypes,
  highlightedNodes,
}: GraphLoaderProps) {
  const loadGraph = useLoadGraph();
  const registerEvents = useRegisterEvents();
  const sigma = useSigma();
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);
  const mousePosRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const { theme } = useTheme();

  // Build graph: nodes, edges, sizing, parallel edge indexing, layout
  useEffect(() => {
    const graph = new MultiGraph();

    // Capture positions from the current graph so existing nodes stay put
    const currentGraph = sigma.getGraph();
    const prevPos = new Map<string, { x: number; y: number }>();
    if (currentGraph.order > 0) {
      currentGraph.forEachNode((n) => {
        prevPos.set(n, {
          x: currentGraph.getNodeAttribute(n, "x"),
          y: currentGraph.getNodeAttribute(n, "y"),
        });
      });
    }
    const isIncremental = prevPos.size > 0;

    // Pre-build adjacency for placing new nodes near neighbors
    const adj = new Map<string, string[]>();
    if (isIncremental) {
      data.edges.forEach((e) => {
        if (!adj.has(e.source)) adj.set(e.source, []);
        if (!adj.has(e.target)) adj.set(e.target, []);
        adj.get(e.source)!.push(e.target);
        adj.get(e.target)!.push(e.source);
      });
    }

    let hasNewNodes = false;

    data.nodes.forEach((node) => {
      if (!graph.hasNode(node.id)) {
        const prev = prevPos.get(node.id);
        let x: number, y: number;

        if (prev) {
          x = prev.x;
          y = prev.y;
        } else if (isIncremental) {
          hasNewNodes = true;
          const nbrs = (adj.get(node.id) || [])
            .filter((id) => prevPos.has(id))
            .map((id) => prevPos.get(id)!);
          if (nbrs.length > 0) {
            const cx = nbrs.reduce((s, p) => s + p.x, 0) / nbrs.length;
            const cy = nbrs.reduce((s, p) => s + p.y, 0) / nbrs.length;
            const angle = Math.random() * 2 * Math.PI;
            const radius = 5 + Math.random() * 10;
            x = cx + Math.cos(angle) * radius;
            y = cy + Math.sin(angle) * radius;
          } else {
            x = Math.random() * 100;
            y = Math.random() * 100;
          }
        } else {
          x = Math.random() * 100;
          y = Math.random() * 100;
        }

        const shape = NODE_SHAPES[node.type] || "circle";
        const color = NODE_COLORS[node.type] || "#666";
        graph.addNode(node.id, {
          label: node.label,
          x,
          y,
          size: NODE_SIZES[node.type] || 5,
          color,
          type: shape,
          nodeType: node.type,
          hidden: !visibleTypes.has(node.type),
          borderColor: shape === "bordered" ? lightenColor(color, 0.6) : undefined,
          riskScore: node.risk_score ?? null,
          keyProp: getKeyProp(node.type, node.properties),
          fixed: isIncremental && prev != null,
        });
      }
    });

    // Build a label lookup for edge metadata
    const labelMap = new Map<string, string>();
    data.nodes.forEach((n) => labelMap.set(n.id, n.label));

    data.edges.forEach((edge) => {
      if (graph.hasNode(edge.source) && graph.hasNode(edge.target)) {
        graph.addEdgeWithKey(edge.id, edge.source, edge.target, {
          label: edge.type.replace(/_/g, " "),
          color: withAlpha(edgeColor(edge.type, theme === "dark"), theme === "dark" ? 0.25 : 0.8),
          size: edgeSizeFromValue(edge.properties),
          edgeType: edge.type,
          sourceLabel: labelMap.get(edge.source) || "",
          targetLabel: labelMap.get(edge.target) || "",
        });
      }
    });

    // Index parallel edges for curvature
    indexParallelEdgesIndex(graph);

    // Degree-based node sizing: hubs get larger, leaves stay small
    let maxDegree = 1;
    graph.forEachNode((node) => {
      const d = graph.degree(node);
      if (d > maxDegree) maxDegree = d;
    });
    graph.forEachNode((node) => {
      const baseSize = graph.getNodeAttribute(node, "size") as number;
      const degree = graph.degree(node);
      const scale = 0.6 + 2.0 * (Math.log(1 + degree) / Math.log(1 + maxDegree));
      graph.setNodeAttribute(node, "size", baseSize * scale);
    });

    // Louvain community detection — assign communities before layout
    if (!isIncremental && graph.order > 2) {
      // Louvain needs a simple graph — create a projection
      const simple = new Graph();
      graph.forEachNode((n, attrs) => simple.addNode(n, attrs));
      graph.forEachEdge((_e, _attrs, src, tgt) => {
        if (src !== tgt && !simple.hasEdge(src, tgt)) {
          simple.addEdge(src, tgt);
        }
      });
      try {
        const communities = louvain(simple);
        Object.entries(communities).forEach(([node, community]) => {
          graph.setNodeAttribute(node, "community", String(community));
        });
        // Seed positions using circlepack grouped by community
        circlepack.assign(graph, {
          hierarchyAttributes: ["community"],
          scale: 800,
        });
      } catch {
        // Fallback: spread randomly if community detection fails
        graph.forEachNode((node) => {
          graph.setNodeAttribute(node, "x", (Math.random() - 0.5) * 1000);
          graph.setNodeAttribute(node, "y", (Math.random() - 0.5) * 1000);
        });
      }
    }

    loadGraph(graph);

    const fa2Settings = {
      gravity: 1,
      scalingRatio: 80,
      linLogMode: true,
      adjustSizes: true,
      slowDown: 8,
      barnesHutOptimize: true,
      strongGravityMode: true,
    };

    if (isIncremental && hasNewNodes) {
      forceAtlas2.assign(graph, {
        iterations: 60,
        settings: { ...fa2Settings, gravity: 2, slowDown: 15 },
      });
      graph.forEachNode((n) => graph.removeNodeAttribute(n, "fixed"));
    } else if (!isIncremental) {
      // Few iterations: refine within-cluster positions without collapsing inter-cluster gaps
      forceAtlas2.assign(graph, {
        iterations: 100,
        settings: fa2Settings,
      });
    }

    sigma.refresh();

    // Auto-fit the camera to show all nodes with padding
    requestAnimationFrame(() => {
      sigma.getCamera().animatedReset({ duration: 0 });
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps -- theme and visibleTypes handled by dedicated effects below
  }, [data, loadGraph, sigma]);

  // Update edge colors when theme changes (without rebuilding layout)
  useEffect(() => {
    const graph = sigma.getGraph();
    if (graph.order === 0) return;
    const isDark = theme === "dark";
    const alpha = isDark ? 0.25 : 0.8;
    graph.forEachEdge((edge) => {
      const edgeType = graph.getEdgeAttribute(edge, "edgeType") as string;
      graph.setEdgeAttribute(edge, "color", withAlpha(edgeColor(edgeType, isDark), alpha));
    });
    sigma.refresh();
  }, [theme, sigma]);

  // Type visibility: update hidden attribute when filters change
  useEffect(() => {
    const graph = sigma.getGraph();
    graph.forEachNode((node) => {
      const nodeType = graph.getNodeAttribute(node, "nodeType") as NodeType;
      graph.setNodeAttribute(node, "hidden", !visibleTypes.has(nodeType));
    });
    sigma.refresh();
  }, [visibleTypes, sigma]);

  // Visual reducers: hover highlighting, path highlighting, risk glow
  useEffect(() => {
    const graph = sigma.getGraph();

    sigma.setSetting("nodeReducer", (node, data) => {
      const res = { ...data };

      // Hover: highlight hovered node + 1-hop neighbors, dim everything else
      if (hoveredNode) {
        if (node === hoveredNode) {
          res.zIndex = 2;
          res.highlighted = true;
        } else if (graph.areNeighbors(node, hoveredNode)) {
          res.zIndex = 1;
        } else {
          const baseColor = NODE_COLORS[graph.getNodeAttribute(node, "nodeType") as NodeType] || "#666";
          res.color = baseColor + "15";
          res.label = "";
          res.zIndex = 0;
        }
      }
      // Path highlighting (from search/chat graph context)
      else if (highlightedNodes && highlightedNodes.size > 0) {
        if (!highlightedNodes.has(node)) {
          const baseColor = NODE_COLORS[graph.getNodeAttribute(node, "nodeType") as NodeType] || "#666";
          res.color = baseColor + "40";
        }
      }

      // Risk glow: red/amber border for high-risk entities
      if (!res.hidden) {
        const riskScore = graph.getNodeAttribute(node, "riskScore") as number | null;
        if (riskScore != null && riskScore >= 0.7) {
          if (data.type === "circle") {
            res.type = "bordered";
            res.borderColor = "#ef4444";
          }
          res.size = (res.size || 5) * 1.15;
        } else if (riskScore != null && riskScore >= 0.5) {
          if (data.type === "circle") {
            res.type = "bordered";
            res.borderColor = "#f59e0b";
          }
        }
      }

      return res;
    });

    sigma.setSetting("edgeReducer", (edge, data) => {
      if (!hoveredNode) return data;
      const [src, tgt] = graph.extremities(edge);
      if (src === hoveredNode || tgt === hoveredNode) {
        // Restore full opacity and thicken connected edges
        const edgeType = graph.getEdgeAttribute(edge, "edgeType") as string;
        const fullColor = EDGE_COLORS[edgeType] || "#333";
        return { ...data, color: fullColor, size: Math.max(data.size || 0.4, 2.5), zIndex: 1 };
      }
      return { ...data, hidden: true };
    });

    sigma.refresh({ skipIndexation: true });
  }, [hoveredNode, highlightedNodes, sigma]);

  // Track mouse position within the sigma container
  useEffect(() => {
    const container = sigma.getContainer();
    const handleMouseMove = (e: MouseEvent) => {
      const rect = container.getBoundingClientRect();
      mousePosRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };
    container.addEventListener("mousemove", handleMouseMove);
    return () => container.removeEventListener("mousemove", handleMouseMove);
  }, [sigma]);

  useEffect(() => {
    registerEvents({
      clickNode: (event) => onNodeClick?.(event.node),
      clickEdge: (event) => onEdgeClick?.(event.edge),
      enterNode: (event) => {
        setHoveredNode(event.node);
        setHoveredEdge(null);
        const container = sigma.getContainer();
        container.style.cursor = "pointer";
      },
      leaveNode: () => {
        setHoveredNode(null);
        const container = sigma.getContainer();
        container.style.cursor = "default";
      },
      enterEdge: (event) => {
        setHoveredEdge(event.edge);
        setHoveredNode(null);
        const container = sigma.getContainer();
        container.style.cursor = "pointer";
      },
      leaveEdge: () => {
        setHoveredEdge(null);
        const container = sigma.getContainer();
        container.style.cursor = "default";
      },
    });
  }, [registerEvents, onNodeClick, onEdgeClick, sigma]);

  // Combined tooltip for nodes and edges, positioned near cursor
  useEffect(() => {
    const container = sigma.getContainer();
    const existingTooltip = container.querySelector(".graph-tooltip");
    if (existingTooltip) existingTooltip.remove();

    const activeId = hoveredNode || hoveredEdge;
    if (!activeId) return;

    const graph = sigma.getGraph();
    const { x, y } = mousePosRef.current;
    const containerRect = container.getBoundingClientRect();

    let html = "";

    if (hoveredNode && graph.hasNode(hoveredNode)) {
      const label = graph.getNodeAttribute(hoveredNode, "label") as string;
      const type = graph.getNodeAttribute(hoveredNode, "nodeType") as NodeType;
      const color = NODE_COLORS[type] || "#666";
      const shape = NODE_SHAPES[type] || "circle";
      const riskScore = graph.getNodeAttribute(hoveredNode, "riskScore") as number | null;
      const keyProp = graph.getNodeAttribute(hoveredNode, "keyProp") as string | null;
      const degree = graph.degree(hoveredNode);
      const shapeIcon = tooltipShapeSvg(shape, color);

      let riskBadge = "";
      if (riskScore != null && riskScore > 0) {
        const pct = Math.round(riskScore * 100);
        const riskColor = riskScore >= 0.7 ? "#ef4444" : riskScore >= 0.5 ? "#f59e0b" : "#22c55e";
        riskBadge = `<span style="background:${riskColor}20;color:${riskColor};padding:1px 6px;border-radius:8px;font-size:10px;font-weight:600;">Risk ${pct}%</span>`;
      }

      html = `
        <div style="display:flex;align-items:center;gap:8px;">
          ${shapeIcon}
          <div style="min-width:0;">
            <div style="font-weight:600;line-height:1.3;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:240px;">${label}</div>
            <div style="display:flex;align-items:center;gap:6px;margin-top:2px;">
              <span style="font-size:11px;color:var(--tooltip-text-muted);">${type}</span>
              ${riskBadge}
            </div>
          </div>
        </div>
        ${keyProp ? `<div style="font-size:11px;color:var(--tooltip-text-muted);margin-top:4px;">${keyProp}</div>` : ""}
        <div style="font-size:10px;color:var(--tooltip-text-muted);margin-top:3px;">${degree} connection${degree !== 1 ? "s" : ""}</div>
      `;
    } else if (hoveredEdge && graph.hasEdge(hoveredEdge)) {
      const edgeType = graph.getEdgeAttribute(hoveredEdge, "edgeType") as string;
      const sourceLabel = graph.getEdgeAttribute(hoveredEdge, "sourceLabel") as string;
      const targetLabel = graph.getEdgeAttribute(hoveredEdge, "targetLabel") as string;
      const displayType = edgeType.replace(/_/g, " ");
      const explanation = EDGE_EXPLANATIONS[edgeType] || "";

      html = `
        <div style="font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;color:var(--tooltip-text-muted);">${displayType}</div>
        <div style="margin-top:3px;font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px;">
          ${sourceLabel} <span style="color:var(--tooltip-text-muted);">&rarr;</span> ${targetLabel}
        </div>
        ${explanation ? `<div style="font-size:11px;color:var(--tooltip-text-muted);margin-top:4px;line-height:1.4;max-width:280px;white-space:normal;">${explanation}</div>` : ""}
      `;
    }

    if (!html) return;

    const tooltip = document.createElement("div");
    tooltip.className = "graph-tooltip";

    const tooltipWidth = 300;
    const tooltipHeight = 120;
    let left = x + 16;
    let top = y + 16;
    if (left + tooltipWidth > containerRect.width) left = x - tooltipWidth - 8;
    if (top + tooltipHeight > containerRect.height) top = y - tooltipHeight - 8;
    left = Math.max(8, left);
    top = Math.max(8, top);

    tooltip.style.cssText = `
      position: absolute;
      top: ${top}px;
      left: ${left}px;
      background: var(--tooltip-bg);
      border: 1px solid var(--tooltip-border);
      border-radius: 12px;
      padding: 8px 12px;
      font-size: 13px;
      color: var(--tooltip-text);
      pointer-events: none;
      z-index: 1000;
      backdrop-filter: blur(12px);
      box-shadow: var(--tooltip-shadow);
      font-family: Inter, system-ui, sans-serif;
      max-width: ${tooltipWidth}px;
    `;
    tooltip.innerHTML = html;
    container.appendChild(tooltip);
  }, [hoveredNode, hoveredEdge, sigma]);

  return null;
}

interface GraphCanvasProps {
  data: GraphData;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  visibleTypes?: Set<NodeType>;
  highlightedNodes?: Set<string>;
}

export default function GraphCanvas({
  data,
  onNodeClick,
  onEdgeClick,
  visibleTypes = new Set(Object.keys(NODE_COLORS) as NodeType[]),
  highlightedNodes,
}: GraphCanvasProps) {
  const { theme } = useTheme();

  const graphBg = theme === "dark" ? "#09090b" : "#f0f0f3";
  const labelColor = theme === "dark" ? "#a1a1aa" : "#64748b";
  const edgeLabelColor = theme === "dark" ? "#71717a" : "#475569";
  const defaultEdgeColor = theme === "dark" ? "#333" : "#64748b";

  if (data.nodes.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center">
        <p className="text-sm" style={{ color: "var(--color-text-muted)" }}>
          No graph data available
        </p>
      </div>
    );
  }

  return (
    <SigmaContainer
      graph={MultiGraph}
      style={{ height: "100%", width: "100%", background: graphBg }}
      settings={{
        renderEdgeLabels: true,
        defaultNodeColor: "#666",
        defaultEdgeColor: withAlpha(defaultEdgeColor, theme === "dark" ? 0.25 : 0.8),
        defaultNodeType: "circle",
        defaultEdgeType: "curvedArrow",
        edgeProgramClasses: {
          curvedArrow: EdgeCurvedArrowProgram,
        },
        nodeProgramClasses: {
          circle: NodeCircleProgram,
          square: NodeSquareProgram,
          diamond: NodeDiamondProgram,
          triangle: NodeTriangleProgram,
          bordered: NodeBorderedProgram,
        },
        labelFont: "Inter, system-ui, sans-serif",
        labelSize: 11,
        labelWeight: "500",
        labelColor: { color: labelColor },
        edgeLabelSize: 11,
        edgeLabelColor: { color: edgeLabelColor },
        labelDensity: 0.15,
        labelGridCellSize: 200,
        labelRenderedSizeThreshold: 5,
        zIndex: true,
      }}
    >
      <GraphLoader
        data={data}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        visibleTypes={visibleTypes}
        highlightedNodes={highlightedNodes}
      />
    </SigmaContainer>
  );
}
