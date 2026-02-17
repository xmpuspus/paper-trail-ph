"use client";

import { useState, useEffect, useMemo } from "react";
import dynamic from "next/dynamic";
import type { GraphData, GraphNode, GraphEdge, NodeType } from "@/types/graph";
import { fetchGraph, getPath } from "@/lib/api";
import Header from "@/components/common/Header";
import GraphControls from "@/components/graph/GraphControls";
import NodeDetail from "@/components/graph/NodeDetail";
import EdgeDetail from "@/components/graph/EdgeDetail";
import Legend from "@/components/graph/Legend";
import ChatPanel from "@/components/chat/ChatPanel";
import { GraphLoadingState } from "@/components/common/Loading";
import { NODE_COLORS, INSIGHT_BANNERS } from "@/lib/constants";

const GraphCanvas = dynamic(() => import("@/components/graph/GraphCanvas"), {
  ssr: false,
  loading: () => <GraphLoadingState />,
});

type RightPanel = "none" | "chat" | "detail";

function bfsPath(data: GraphData, fromId: string, toId: string): string[] | null {
  const adj = new Map<string, string[]>();
  data.edges.forEach((e) => {
    if (!adj.has(e.source)) adj.set(e.source, []);
    if (!adj.has(e.target)) adj.set(e.target, []);
    adj.get(e.source)!.push(e.target);
    adj.get(e.target)!.push(e.source);
  });
  const visited = new Set<string>([fromId]);
  const queue: string[][] = [[fromId]];
  while (queue.length > 0) {
    const path = queue.shift()!;
    const current = path[path.length - 1];
    if (current === toId) return path;
    for (const nb of adj.get(current) || []) {
      if (!visited.has(nb)) {
        visited.add(nb);
        queue.push([...path, nb]);
      }
    }
  }
  return null;
}

export default function Home() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], edges: [] });
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);

  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<GraphEdge | null>(null);

  const [showFilters, setShowFilters] = useState(false);
  const [rightPanel, setRightPanel] = useState<RightPanel>("none");

  const [visibleNodeTypes, setVisibleNodeTypes] = useState<Set<NodeType>>(
    new Set(Object.keys(NODE_COLORS) as NodeType[])
  );
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [pathMode, setPathMode] = useState<{ sourceId: string; sourceLabel: string } | null>(null);
  const [pendingChatQuery, setPendingChatQuery] = useState<string | null>(null);

  const loadInitialData = async () => {
    setLoading(true);
    setLoadError(false);
    try {
      const data = await fetchGraph(undefined, 1);
      setGraphData(data);
    } catch (error) {
      console.error("Failed to fetch graph data:", error);
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleNodeClick = async (nodeId: string) => {
    if (pathMode) {
      if (nodeId === pathMode.sourceId) {
        setPathMode(null);
        return;
      }
      try {
        const result = await getPath(pathMode.sourceId, nodeId);
        setGraphData((prev) => {
          const nodeIds = new Set(prev.nodes.map((n) => n.id));
          const edgeIds = new Set(prev.edges.map((e) => e.id));
          return {
            nodes: [...prev.nodes, ...result.nodes.filter((n) => !nodeIds.has(n.id))],
            edges: [...prev.edges, ...result.edges.filter((e) => !edgeIds.has(e.id))],
          };
        });
        setHighlightedNodes(new Set(result.nodes.map((n) => n.id)));
      } catch {
        // Fall back to client-side BFS if API is unavailable
        const path = bfsPath(graphData, pathMode.sourceId, nodeId);
        if (path) setHighlightedNodes(new Set(path));
      }
      setPathMode(null);
      return;
    }

    const node = graphData.nodes.find((n) => n.id === nodeId);
    if (node) {
      setSelectedNode(node);
      setSelectedEdge(null);
      setRightPanel("detail");
    }
  };

  const handleExpand = async (nodeId: string) => {
    try {
      const subgraph = await fetchGraph(nodeId, 2);
      setGraphData((prev) => {
        const nodeIds = new Set(prev.nodes.map((n) => n.id));
        const edgeIds = new Set(prev.edges.map((e) => e.id));
        return {
          nodes: [...prev.nodes, ...subgraph.nodes.filter((n) => !nodeIds.has(n.id))],
          edges: [...prev.edges, ...subgraph.edges.filter((e) => !edgeIds.has(e.id))],
        };
      });
      setHighlightedNodes(new Set(subgraph.nodes.map((n) => n.id)));
    } catch {
      // Fall back to highlighting existing neighbors
      const connected = new Set<string>([nodeId]);
      graphData.edges.forEach((e) => {
        if (e.source === nodeId) connected.add(e.target);
        if (e.target === nodeId) connected.add(e.source);
      });
      setHighlightedNodes(connected);
    }
  };

  const handleFindPath = (nodeId: string) => {
    const node = graphData.nodes.find((n) => n.id === nodeId);
    setPathMode({ sourceId: nodeId, sourceLabel: node?.label || nodeId });
    setRightPanel("none");
    setSelectedNode(null);
    setSelectedEdge(null);
  };

  // Cancel path mode on Escape
  useEffect(() => {
    if (!pathMode) return;
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setPathMode(null);
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [pathMode]);

  const handleEdgeClick = (edgeId: string) => {
    const edge = graphData.edges.find((e) => e.id === edgeId);
    if (edge) {
      setSelectedEdge(edge);
      setSelectedNode(null);
      setRightPanel("detail");
    }
  };

  const handleSearchSelect = (nodeId: string) => {
    handleNodeClick(nodeId);
  };

  const handleNodeTypeToggle = (type: NodeType) => {
    setVisibleNodeTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  };

  const handleChatToggle = () => {
    setRightPanel((prev) => (prev === "chat" ? "none" : "chat"));
  };

  const handleDetailClose = () => {
    setSelectedNode(null);
    setSelectedEdge(null);
    setRightPanel("none");
  };

  const handleChatGraphContext = (context: GraphData) => {
    if (context.nodes.length > 0) {
      const nodeIds = new Set(context.nodes.map((n) => n.id));
      setHighlightedNodes(nodeIds);
    }
  };

  const neighborCounts = useMemo(() => {
    if (!selectedNode) return undefined;

    const counts: Record<string, number> = {};
    graphData.edges.forEach((edge) => {
      if (edge.source === selectedNode.id) {
        const targetNode = graphData.nodes.find((n) => n.id === edge.target);
        if (targetNode) {
          counts[targetNode.type] = (counts[targetNode.type] || 0) + 1;
        }
      } else if (edge.target === selectedNode.id) {
        const sourceNode = graphData.nodes.find((n) => n.id === edge.source);
        if (sourceNode) {
          counts[sourceNode.type] = (counts[sourceNode.type] || 0) + 1;
        }
      }
    });
    return counts;
  }, [selectedNode, graphData]);

  const selectedEdgeNodes = useMemo(() => {
    if (!selectedEdge) return { source: undefined, target: undefined };
    return {
      source: graphData.nodes.find((n) => n.id === selectedEdge.source),
      target: graphData.nodes.find((n) => n.id === selectedEdge.target),
    };
  }, [selectedEdge, graphData]);

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      {/* Header */}
      <div className="pt-7">
        <Header
          onSearchSelect={handleSearchSelect}
          onFilterToggle={() => setShowFilters(!showFilters)}
          onChatToggle={handleChatToggle}
          showFilters={showFilters}
          showChat={rightPanel === "chat"}
        />
      </div>

      {/* Error banner */}
      {loadError && (
        <div
          className="flex items-center justify-center gap-3 px-4 py-1.5 text-center text-xs"
          style={{
            borderBottom: "1px solid var(--color-border)",
            backgroundColor: "rgba(239, 68, 68, 0.05)",
            color: "var(--color-text-secondary)",
          }}
        >
          <span>Server may be waking up (free tier cold start) — give it a moment</span>
          <button
            onClick={loadInitialData}
            className="rounded px-2 py-0.5 text-xs font-medium transition-colors"
            style={{
              backgroundColor: "var(--color-accent)",
              color: "#fff",
            }}
          >
            Retry
          </button>
        </div>
      )}

      {/* Main area: graph full-bleed with floating panels */}
      <div className="relative flex-1 overflow-hidden">
        {/* Graph canvas — always fills the entire space */}
        {loading ? (
          <GraphLoadingState />
        ) : (
          <GraphCanvas
            data={graphData}
            onNodeClick={handleNodeClick}
            onEdgeClick={handleEdgeClick}
            visibleTypes={visibleNodeTypes}
            highlightedNodes={highlightedNodes}
          />
        )}

        {/* Path mode banner or Insight ticker — top center */}
        {!loading && pathMode && (
          <div className="absolute left-1/2 top-3 z-30 -translate-x-1/2">
            <div
              className="glass-panel-elevated flex items-center gap-3 rounded-full px-4 py-2.5"
              style={{ maxWidth: "min(600px, 90vw)" }}
            >
              <span
                className="flex-shrink-0 text-[10px] font-bold uppercase tracking-widest"
                style={{ color: "var(--color-accent)" }}
              >
                Path
              </span>
              <span className="truncate text-xs" style={{ color: "var(--color-text-secondary)" }}>
                Click a node to find path from <strong>{pathMode.sourceLabel}</strong>
              </span>
              <button
                onClick={() => setPathMode(null)}
                className="flex-shrink-0 text-[10px] font-medium"
                style={{ color: "var(--color-text-muted)" }}
              >
                Esc to cancel
              </button>
            </div>
          </div>
        )}
        {!loading && !pathMode && rightPanel !== "chat" && (
          <div className="absolute left-1/2 top-3 z-10 -translate-x-1/2">
            <button
              onClick={() => {
                const banner = INSIGHT_BANNERS[Math.floor(Date.now() / 10000) % INSIGHT_BANNERS.length];
                setPendingChatQuery(banner.query);
                setRightPanel("chat");
              }}
              className="glass-panel flex items-center gap-3 rounded-full px-4 py-2 transition-all duration-200"
              style={{ maxWidth: "min(600px, 90vw)" }}
            >
              <span
                className="flex-shrink-0 text-[10px] font-bold uppercase tracking-widest"
                style={{ color: "var(--color-accent)" }}
              >
                Insight
              </span>
              <span
                className="truncate text-xs"
                style={{ color: "var(--color-text-secondary)" }}
              >
                {INSIGHT_BANNERS[Math.floor(Date.now() / 10000) % INSIGHT_BANNERS.length].text}
              </span>
              <span
                className="flex-shrink-0 text-[10px]"
                style={{ color: "var(--color-text-muted)" }}
              >
                Ask &rarr;
              </span>
            </button>
          </div>
        )}

        {/* Floating filters panel — left side */}
        {showFilters && (
          <div className="absolute left-3 top-3 z-20 w-60 animate-slide-in-left">
            <div className="glass-panel-elevated custom-scrollbar max-h-[calc(100vh-10rem)] overflow-y-auto rounded-2xl p-4">
              <GraphControls
                nodeTypeFilter={visibleNodeTypes}
                onNodeTypeToggle={handleNodeTypeToggle}
                nodeCount={graphData.nodes.filter((n) => visibleNodeTypes.has(n.type)).length}
                edgeCount={graphData.edges.length}
              />
            </div>
          </div>
        )}

        {/* Floating right panel — chat or detail */}
        {rightPanel === "detail" && (selectedNode || selectedEdge) && (
          <div className="absolute right-3 top-3 bottom-3 z-20 w-[380px] animate-slide-in-right">
            <div className="glass-panel-elevated custom-scrollbar h-full overflow-y-auto rounded-2xl">
              {selectedNode && (
                <NodeDetail
                  node={selectedNode}
                  neighborCounts={neighborCounts}
                  onClose={handleDetailClose}
                  onExpand={handleExpand}
                  onFindPath={handleFindPath}
                />
              )}
              {selectedEdge && (
                <EdgeDetail
                  edge={selectedEdge}
                  sourceNode={selectedEdgeNodes.source}
                  targetNode={selectedEdgeNodes.target}
                  onClose={handleDetailClose}
                />
              )}
            </div>
          </div>
        )}

        {rightPanel === "chat" && (
          <div className="absolute right-3 top-3 bottom-3 z-20 w-[420px] animate-slide-in-right">
            <div className="glass-panel-elevated flex h-full flex-col rounded-2xl">
              <ChatPanel
                onClose={() => setRightPanel("none")}
                onGraphContext={handleChatGraphContext}
                focusedNodeId={selectedNode?.id}
                visibleNodeIds={graphData.nodes
                  .filter((n) => visibleNodeTypes.has(n.type))
                  .map((n) => n.id)}
                initialQuery={pendingChatQuery}
                onInitialQueryConsumed={() => setPendingChatQuery(null)}
              />
            </div>
          </div>
        )}

        {/* Legend — bottom of graph */}
        {!loading && (
          <div className="absolute bottom-3 left-3 right-3 z-10">
            <Legend visibleTypes={visibleNodeTypes} onToggleType={handleNodeTypeToggle} />
          </div>
        )}
      </div>
    </div>
  );
}
