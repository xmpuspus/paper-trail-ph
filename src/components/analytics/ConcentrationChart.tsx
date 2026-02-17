"use client";

import { formatCompact } from "@/lib/constants";

interface ConcentrationData {
  name: string;
  value: number;
  percentage: number;
}

interface ConcentrationChartProps {
  data: ConcentrationData[];
  maxItems?: number;
}

export default function ConcentrationChart({ data, maxItems = 10 }: ConcentrationChartProps) {
  const displayData = data.slice(0, maxItems);
  const maxValue = Math.max(...displayData.map((d) => d.value));

  return (
    <div className="space-y-2">
      {displayData.map((item, index) => (
        <div key={index} className="space-y-1">
          <div className="flex items-baseline justify-between text-xs">
            <span
              className="truncate font-mono"
              style={{ color: "var(--color-text-secondary)" }}
            >
              {item.name}
            </span>
            <span
              className="ml-2 flex-shrink-0 font-mono"
              style={{ color: "var(--color-text-muted)" }}
            >
              {formatCompact(item.value)} ({item.percentage.toFixed(1)}%)
            </span>
          </div>
          <div
            className="h-6 w-full overflow-hidden rounded-sm"
            style={{ backgroundColor: "var(--chart-bar-bg)" }}
          >
            <div
              className="h-full bg-gradient-to-r from-contractor to-contractor/70 transition-all duration-300"
              style={{ width: `${(item.value / maxValue) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
