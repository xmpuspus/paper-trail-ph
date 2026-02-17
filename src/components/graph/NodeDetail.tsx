"use client";

import { useState } from "react";
import type { GraphNode } from "@/types/graph";
import { X, ArrowsOut, Path } from "@phosphor-icons/react";
import { NODE_COLORS, NODE_LABELS, formatPeso } from "@/lib/constants";
import RedFlagBadge from "@/components/analytics/RedFlagBadge";
import AgencyDashboard from "@/components/analytics/AgencyDashboard";
import ContractorProfile from "@/components/analytics/ContractorProfile";

function getNodeInsight(node: GraphNode): string | null {
  const { type, properties, risk_score, red_flags } = node;

  if (type === "Contractor") {
    if (risk_score && risk_score >= 0.7) {
      const singleBidder = red_flags?.find((f) => f.type === "single_bidder");
      if (singleBidder) {
        return `This contractor shows a high single-bidder rate. In competitive procurement, consistently being the only bidder may indicate market manipulation or specifications tailored to a single vendor.`;
      }
      return `Risk score of ${(risk_score * 100).toFixed(0)}% is above the 70% threshold. Multiple red flags suggest this contractor warrants deeper investigation into its procurement history and ownership structure.`;
    }
    const collusion = red_flags?.find((f) => f.type === "collusion_ring");
    if (collusion) {
      return `Flagged for potential bid rotation. When two contractors repeatedly co-bid and alternate wins, it may indicate coordinated bidding rather than genuine competition.`;
    }
  }

  if (type === "Contract") {
    const method = properties.procurement_method;
    if (method === "Negotiated Procurement") {
      return `Negotiated procurement bypasses competitive bidding. While legal for emergencies and small amounts, it's frequently used to circumvent transparency requirements. Check if the justification matches RA 9184 criteria.`;
    }
    if (red_flags && red_flags.length > 0) {
      return `This contract has been flagged. Cross-reference with the winning contractor's other contracts and the procuring agency's concentration metrics for patterns.`;
    }
  }

  if (type === "Agency") {
    return `View this agency's procurement concentration (HHI score) below. An HHI above 0.25 means the agency's spending is concentrated among few contractors, potentially limiting competition.`;
  }

  if (type === "AuditFinding") {
    const isRepeat = red_flags?.find((f) => f.type === "audit_repeat");
    if (isRepeat) {
      return `Repeat audit finding. When COA flags the same issue in consecutive years, it indicates the agency has not addressed the root cause. This is a serious governance concern.`;
    }
    return `Commission on Audit findings are official government records. They identify irregularities in spending and procurement that may require corrective action.`;
  }

  if (type === "PoliticalFamily") {
    const positions = properties.positions_held;
    const munis = properties.municipalities;
    if (positions && munis) {
      return `This family holds ${positions} government positions across ${Array.isArray(munis) ? munis.length : 1} municipalities. The Philippines has no anti-dynasty law, allowing families to consolidate political power across jurisdictions.`;
    }
  }

  if (type === "Politician") {
    return `Check this official's connections to contractors and political families. Conflicts of interest arise when officials have authority over procurement that benefits their associates.`;
  }

  return null;
}

interface NodeDetailProps {
  node: GraphNode;
  neighborCounts?: Record<string, number>;
  onClose: () => void;
  onExpand?: (nodeId: string) => void;
  onFindPath?: (nodeId: string) => void;
}

export default function NodeDetail({
  node,
  neighborCounts,
  onClose,
  onExpand,
  onFindPath,
}: NodeDetailProps) {
  const [showAnalytics] = useState(true);
  const shouldShowAnalytics = node.type === "Agency" || node.type === "Contractor";

  return (
    <div className="detail-panel h-full">
      {/* Header */}
      <div className="mb-5 flex items-start justify-between">
        <div className="min-w-0 flex-1">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <div
              className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold text-white"
              style={{ backgroundColor: NODE_COLORS[node.type] }}
            >
              {NODE_LABELS[node.type]}
            </div>
            {node.risk_score !== undefined && (
              <div
                className="inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
                style={{
                  backgroundColor:
                    node.risk_score >= 0.7
                      ? "var(--badge-risk-high-bg)"
                      : node.risk_score >= 0.5
                        ? "var(--badge-risk-medium-bg)"
                        : "var(--badge-risk-low-bg)",
                  color:
                    node.risk_score >= 0.7
                      ? "var(--badge-risk-high-text)"
                      : node.risk_score >= 0.5
                        ? "var(--badge-risk-medium-text)"
                        : "var(--badge-risk-low-text)",
                }}
              >
                Risk: {(node.risk_score * 100).toFixed(0)}%
              </div>
            )}
          </div>
          <h3
            className="text-base font-semibold leading-snug break-words"
            style={{ color: "var(--color-text-primary)" }}
          >
            {node.label}
          </h3>
        </div>
        <button onClick={onClose} className="btn-ghost ml-2 flex-shrink-0">
          <X size={16} weight="bold" />
        </button>
      </div>

      <div className="space-y-5">
        {/* Contextual insight */}
        {getNodeInsight(node) && (
          <div
            className="rounded-lg p-3 text-xs leading-relaxed"
            style={{
              backgroundColor: "var(--color-surface)",
              border: "1px solid var(--color-border)",
              color: "var(--color-text-secondary)",
            }}
          >
            <p
              className="mb-1 text-[10px] font-semibold uppercase tracking-wider"
              style={{ color: "var(--color-text-muted)" }}
            >
              Why this matters
            </p>
            {getNodeInsight(node)}
          </div>
        )}

        {/* Red flags */}
        {node.red_flags && node.red_flags.length > 0 && (
          <div>
            <p
              className="mb-2 text-[11px] font-medium uppercase tracking-wider"
              style={{ color: "var(--color-text-muted)" }}
            >
              Red Flags
            </p>
            <div className="space-y-2">
              {node.red_flags.map((flag, idx) => (
                <RedFlagBadge key={idx} redFlag={flag} />
              ))}
            </div>
          </div>
        )}

        {/* Properties */}
        <div>
          <p
            className="mb-2 text-[11px] font-medium uppercase tracking-wider"
            style={{ color: "var(--color-text-muted)" }}
          >
            Properties
          </p>
          <div className="space-y-0">
            {Object.entries(node.properties).map(([key, value]) => {
              let displayValue = value;
              if (typeof value === "number" && key.toLowerCase().includes("amount")) {
                displayValue = formatPeso(value);
              } else if (typeof value === "object") {
                displayValue = JSON.stringify(value);
              }

              return (
                <div
                  key={key}
                  className="flex justify-between py-2 text-sm last:border-b-0"
                  style={{ borderBottom: "1px solid var(--color-border-subtle)" }}
                >
                  <span style={{ color: "var(--color-text-muted)" }}>
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className="ml-2 flex-1 break-words text-right font-mono text-xs"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    {String(displayValue)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Connections */}
        {neighborCounts && Object.keys(neighborCounts).length > 0 && (
          <div>
            <p
              className="mb-2 text-[11px] font-medium uppercase tracking-wider"
              style={{ color: "var(--color-text-muted)" }}
            >
              Connections
            </p>
            <div className="space-y-0">
              {Object.entries(neighborCounts).map(([type, count]) => (
                <div key={type} className="flex justify-between py-1.5 text-sm">
                  <span style={{ color: "var(--color-text-secondary)" }}>
                    {type.replace(/_/g, " ")}
                  </span>
                  <span
                    className="font-mono text-xs"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    {count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          {onExpand && (
            <button onClick={() => onExpand(node.id)} className="btn-surface flex-1">
              <span className="flex items-center justify-center gap-1.5">
                <ArrowsOut size={14} weight="bold" />
                Expand
              </span>
            </button>
          )}
          {onFindPath && (
            <button onClick={() => onFindPath(node.id)} className="btn-surface flex-1">
              <span className="flex items-center justify-center gap-1.5">
                <Path size={14} weight="bold" />
                Find Path
              </span>
            </button>
          )}
        </div>

        {/* Analytics */}
        {shouldShowAnalytics && showAnalytics && (
          <div className="pt-4" style={{ borderTop: "1px solid var(--color-border)" }}>
            {node.type === "Agency" && <AgencyDashboard agencyId={node.id} />}
            {node.type === "Contractor" && <ContractorProfile contractorId={node.id} />}
          </div>
        )}
      </div>
    </div>
  );
}
