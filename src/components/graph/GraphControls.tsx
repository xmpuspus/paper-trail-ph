"use client";

import type { NodeType } from "@/types/graph";
import { NODE_LABELS, NODE_COLORS, NODE_SHAPES } from "@/lib/constants";

function ShapeIcon({ shape, color, opacity }: { shape: string; color: string; opacity: number }) {
  const s = 10;
  const style = { opacity, flexShrink: 0 };
  switch (shape) {
    case "square":
      return (
        <svg width={s} height={s} style={style}>
          <rect x="0" y="0" width={s} height={s} fill={color} />
        </svg>
      );
    case "diamond":
      return (
        <svg width={s} height={s} style={style}>
          <rect x="1.5" y="1.5" width="7" height="7" fill={color} transform={`rotate(45,${s / 2},${s / 2})`} />
        </svg>
      );
    case "triangle":
      return (
        <svg width={s} height={s} style={style}>
          <polygon points={`${s / 2},0 ${s},${s} 0,${s}`} fill={color} />
        </svg>
      );
    case "bordered":
      return (
        <svg width={s} height={s} style={style}>
          <circle cx={s / 2} cy={s / 2} r={s / 2 - 0.5} fill={color} stroke="rgba(255,255,255,0.5)" strokeWidth="1.5" />
        </svg>
      );
    default:
      return (
        <svg width={s} height={s} style={style}>
          <circle cx={s / 2} cy={s / 2} r={s / 2} fill={color} />
        </svg>
      );
  }
}

interface GraphControlsProps {
  nodeTypeFilter: Set<NodeType>;
  onNodeTypeToggle: (type: NodeType) => void;
  nodeCount: number;
  edgeCount: number;
}

export default function GraphControls({
  nodeTypeFilter,
  onNodeTypeToggle,
  nodeCount,
  edgeCount,
}: GraphControlsProps) {
  const nodeTypes = Object.keys(NODE_LABELS) as NodeType[];

  return (
    <div className="space-y-5">
      {/* Node type filters */}
      <div>
        <p
          className="mb-3 text-[11px] font-medium uppercase tracking-wider"
          style={{ color: "var(--color-text-muted)" }}
        >
          Node Types
        </p>
        <div className="space-y-0.5">
          {nodeTypes.map((type) => {
            const isActive = nodeTypeFilter.has(type);
            return (
              <button
                key={type}
                onClick={() => onNodeTypeToggle(type)}
                className="flex w-full cursor-pointer items-center gap-2.5 rounded-lg px-2 py-1.5 text-sm transition-all duration-150"
                style={{
                  backgroundColor: "transparent",
                }}
              >
                <ShapeIcon
                  shape={NODE_SHAPES[type]}
                  color={NODE_COLORS[type]}
                  opacity={isActive ? 1 : 0.25}
                />
                <span
                  className="transition-colors duration-150"
                  style={{
                    color: isActive
                      ? "var(--color-text-primary)"
                      : "var(--color-text-muted)",
                  }}
                >
                  {NODE_LABELS[type]}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Stats */}
      <div style={{ borderTop: "1px solid var(--color-border)" }} className="pt-4">
        <p
          className="mb-2.5 text-[11px] font-medium uppercase tracking-wider"
          style={{ color: "var(--color-text-muted)" }}
        >
          Stats
        </p>
        <div className="grid grid-cols-2 gap-2">
          <div
            className="rounded-lg px-3 py-2"
            style={{ backgroundColor: "var(--color-input-bg)" }}
          >
            <div
              className="font-mono text-sm font-medium"
              style={{ color: "var(--color-text-primary)" }}
            >
              {nodeCount}
            </div>
            <div className="text-[11px]" style={{ color: "var(--color-text-muted)" }}>
              nodes
            </div>
          </div>
          <div
            className="rounded-lg px-3 py-2"
            style={{ backgroundColor: "var(--color-input-bg)" }}
          >
            <div
              className="font-mono text-sm font-medium"
              style={{ color: "var(--color-text-primary)" }}
            >
              {edgeCount}
            </div>
            <div className="text-[11px]" style={{ color: "var(--color-text-muted)" }}>
              edges
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
