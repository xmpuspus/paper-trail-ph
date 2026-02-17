"use client";

import type { GraphEdge, GraphNode } from "@/types/graph";
import { X } from "@phosphor-icons/react";
import { NODE_COLORS } from "@/lib/constants";
import type { NodeType } from "@/types/graph";

export const EDGE_EXPLANATIONS: Record<string, string> = {
  PROCURED: "This agency initiated and managed the procurement process for this contract.",
  AWARDED_TO: "This contract was awarded to the contractor through the procurement process.",
  BID_ON: "The contractor submitted a bid for this contract. Check the bid amount vs. award amount for patterns.",
  CO_BID_WITH: "These contractors frequently appear in the same bidding processes. Alternating wins may indicate bid rotation.",
  SUBCONTRACTED_TO: "The winning contractor passed part of the work to this subcontractor. Layered subcontracting can obscure the real beneficiary.",
  MEMBER_OF: "This politician belongs to a political family. Look for overlap between family members' jurisdictions and contractor awards.",
  GOVERNS: "This official has authority over the municipality, including oversight of local procurement.",
  AUDITED: "The Commission on Audit reviewed this entity's procurement practices and issued findings.",
  INVOLVES_OFFICIAL: "This audit finding involves or references this contract. A repeat finding signals systemic issues.",
  OWNED_BY: "Ownership relationship. Cross-reference with political connections to identify conflicts of interest.",
  LOCATED_IN: "Geographic relationship. Contractors clustered near procuring agencies may warrant scrutiny.",
  FAMILY_OF: "Family relationship. The Anti-Dynasty Bill (if passed) would restrict relatives from holding simultaneous office.",
  HAS_AGENCY: "This municipality contains or oversees this government agency.",
  AUTHORED: "This legislator authored this bill.",
  CO_AUTHORED_WITH: "These legislators co-authored legislation together.",
  ASSOCIATED_WITH: "General association between these entities.",
  DONATED_TO: "Campaign contribution. When donors later win government contracts, this path reveals potential pay-to-play dynamics.",
  BLACKLISTED: "This contractor was sanctioned by a government agency. Check if related companies continue to win contracts.",
  DECLARED_WEALTH: "Publicly disclosed SALN (Statement of Assets, Liabilities, and Net Worth). Compare across filing years for unusual growth.",
  RE_REGISTERED_AS: "This company re-registered under a new name, often after blacklisting or controversy — a phoenix company indicator.",
  SAME_ADDRESS_AS: "These separate companies share a registered address. Combined with shared directors, this suggests shell company networks.",
  SHARES_DIRECTOR_WITH: "These companies share one or more directors or owners. Cross-reference with contract awards for conflict of interest.",
  ALLIED_WITH: "Political alliance between these officials or families. Check if their jurisdictions steer contracts to the same contractors.",
};

interface EdgeDetailProps {
  edge: GraphEdge;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  onClose: () => void;
}

export default function EdgeDetail({ edge, sourceNode, targetNode, onClose }: EdgeDetailProps) {
  return (
    <div className="detail-panel h-full">
      <div className="mb-5 flex items-start justify-between">
        <div className="flex-1">
          <div
            className="mb-2 inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold"
            style={{
              backgroundColor: "var(--color-input-bg)",
              color: "var(--color-text-secondary)",
            }}
          >
            {edge.type.replace(/_/g, " ")}
          </div>
          <h3
            className="text-base font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Relationship
          </h3>
        </div>
        <button onClick={onClose} className="btn-ghost">
          <X size={16} weight="bold" />
        </button>
      </div>

      <div className="space-y-5">
        {sourceNode && targetNode && (
          <div
            className="rounded-xl p-3"
            style={{
              backgroundColor: "var(--color-input-bg)",
              border: "1px solid var(--color-border)",
            }}
          >
            <div className="flex items-center gap-2.5 text-sm">
              <div
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: NODE_COLORS[sourceNode.type as NodeType] }}
              />
              <span style={{ color: "var(--color-text-primary)" }}>
                {sourceNode.label}
              </span>
              <span style={{ color: "var(--color-text-muted)" }}>-&gt;</span>
              <div
                className="h-2 w-2 flex-shrink-0 rounded-full"
                style={{ backgroundColor: NODE_COLORS[targetNode.type as NodeType] }}
              />
              <span style={{ color: "var(--color-text-primary)" }}>
                {targetNode.label}
              </span>
            </div>
          </div>
        )}

        {/* Relationship explanation */}
        {EDGE_EXPLANATIONS[edge.type] && (
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
              What this means
            </p>
            {EDGE_EXPLANATIONS[edge.type]}
          </div>
        )}

        {Object.keys(edge.properties).length > 0 && (
          <div>
            <p
              className="mb-2 text-[11px] font-medium uppercase tracking-wider"
              style={{ color: "var(--color-text-muted)" }}
            >
              Properties
            </p>
            <div className="space-y-0">
              {Object.entries(edge.properties).map(([key, value]) => (
                <div
                  key={key}
                  className="flex justify-between py-2 text-sm last:border-b-0"
                  style={{ borderBottom: "1px solid var(--color-border-subtle)" }}
                >
                  <span style={{ color: "var(--color-text-muted)" }}>
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className="font-mono text-xs"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    {typeof value === "object" ? JSON.stringify(value) : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
