"use client";

import type { RedFlag } from "@/types/graph";
import { useState } from "react";
import { Warning, WarningCircle, Info, ShieldWarning } from "@phosphor-icons/react";

interface RedFlagBadgeProps {
  redFlag: RedFlag;
  compact?: boolean;
}

const SEVERITY_STYLES = {
  critical: {
    bg: "var(--severity-critical-bg)",
    text: "var(--severity-critical-text)",
    border: "var(--severity-critical-border)",
    icon: ShieldWarning,
  },
  high: {
    bg: "var(--severity-high-bg)",
    text: "var(--severity-high-text)",
    border: "var(--severity-high-border)",
    icon: Warning,
  },
  medium: {
    bg: "var(--severity-medium-bg)",
    text: "var(--severity-medium-text)",
    border: "var(--severity-medium-border)",
    icon: WarningCircle,
  },
  low: {
    bg: "var(--severity-low-bg)",
    text: "var(--severity-low-text)",
    border: "var(--severity-low-border)",
    icon: Info,
  },
};

const FLAG_LABELS: Record<string, string> = {
  single_bidder: "Single Bidder",
  identical_bid_amounts: "Identical Bids",
  rotating_winners: "Rotating Winners",
  split_contracts: "Contract Splitting",
  abnormal_pricing: "Abnormal Pricing",
  geographic_anomaly: "Geographic Anomaly",
  timing_cluster: "Timing Pattern",
  concentration: "High Concentration",
  collusion_ring: "Collusion Ring",
  political_connection: "Political Link",
  shell_network: "Shell Network",
  cross_agency_pattern: "Cross-Agency Pattern",
  audit_repeat: "Repeat Finding",
};

export default function RedFlagBadge({ redFlag, compact = false }: RedFlagBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false);
  const style = SEVERITY_STYLES[redFlag.severity];
  const Icon = style.icon;
  const label = FLAG_LABELS[redFlag.type] || redFlag.type;

  if (compact) {
    return (
      <div className="relative inline-block">
        <div
          onMouseEnter={() => setShowTooltip(true)}
          onMouseLeave={() => setShowTooltip(false)}
          className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium"
          style={{
            backgroundColor: style.bg,
            color: style.text,
            borderColor: style.border,
          }}
        >
          <Icon size={12} weight="fill" />
          <span>{label}</span>
        </div>
        {showTooltip && (
          <div
            className="absolute bottom-full left-1/2 z-50 mb-2 w-64 -translate-x-1/2 rounded-lg border p-3 shadow-xl"
            style={{
              backgroundColor: "var(--flag-tooltip-bg)",
              borderColor: "var(--flag-tooltip-border)",
            }}
          >
            <div
              className="mb-1 text-xs font-semibold"
              style={{ color: "var(--flag-tooltip-title)" }}
            >
              {redFlag.description}
            </div>
            <div className="text-xs" style={{ color: "var(--flag-tooltip-text)" }}>
              {redFlag.evidence}
            </div>
            <div
              className="mt-2 text-xs"
              style={{ color: "var(--flag-tooltip-muted)" }}
            >
              Detected: {new Date(redFlag.detected_at).toLocaleDateString()}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div
      className="flex items-start gap-2 rounded-lg border p-3"
      style={{
        backgroundColor: style.bg,
        borderColor: style.border,
      }}
    >
      <Icon size={20} weight="fill" style={{ color: style.text }} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-semibold" style={{ color: style.text }}>
          {label}
        </div>
        <div
          className="mt-1 text-xs"
          style={{ color: "var(--color-text-secondary)" }}
        >
          {redFlag.description}
        </div>
        <div
          className="mt-1 text-xs"
          style={{ color: "var(--color-text-muted)" }}
        >
          {redFlag.evidence}
        </div>
        <div
          className="mt-2 text-xs"
          style={{ color: "var(--color-text-muted)" }}
        >
          Detected: {new Date(redFlag.detected_at).toLocaleDateString()}
        </div>
      </div>
    </div>
  );
}
