"use client";

import { NODE_COLORS, NODE_LABELS, NODE_SHAPES } from "@/lib/constants";
import type { NodeType } from "@/types/graph";

function ShapeIcon({ shape, color, opacity }: { shape: string; color: string; opacity: number }) {
  const s = 8;
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
          <rect x="1" y="1" width="6" height="6" fill={color} transform={`rotate(45,${s / 2},${s / 2})`} />
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

interface LegendProps {
  visibleTypes: Set<NodeType>;
  onToggleType: (type: NodeType) => void;
}

export default function Legend({ visibleTypes, onToggleType }: LegendProps) {
  const nodeTypes = Object.keys(NODE_COLORS) as NodeType[];

  return (
    <div className="glass-panel inline-flex flex-wrap items-center gap-1 rounded-xl px-2 py-1.5">
      {nodeTypes.map((type) => {
        const isActive = visibleTypes.has(type);
        return (
          <button
            key={type}
            onClick={() => onToggleType(type)}
            className="flex items-center gap-1.5 rounded-md px-2 py-1 text-[11px] transition-all duration-150"
            style={{
              color: isActive
                ? "var(--color-text-secondary)"
                : "var(--color-text-muted)",
            }}
          >
            <ShapeIcon
              shape={NODE_SHAPES[type]}
              color={NODE_COLORS[type]}
              opacity={isActive ? 1 : 0.3}
            />
            {NODE_LABELS[type]}
          </button>
        );
      })}
    </div>
  );
}
