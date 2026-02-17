"use client";

import { useEffect, useState } from "react";
import type { ContractorProfile as ContractorProfileType } from "@/types/api";
import { getContractorProfile } from "@/lib/api";
import { formatCompact } from "@/lib/constants";
import RedFlagBadge from "./RedFlagBadge";
import { Spinner } from "@/components/common/Loading";

interface ContractorProfileProps {
  contractorId: string;
}

export default function ContractorProfile({ contractorId }: ContractorProfileProps) {
  const [data, setData] = useState<ContractorProfileType | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const result = await getContractorProfile(contractorId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load contractor data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [contractorId]);

  if (loading) {
    return (
      <div className="p-6">
        <Spinner />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 text-sm" style={{ color: "var(--badge-risk-high-text)" }}>
        {error || "No data available"}
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div>
        <h3
          className="mb-4 text-lg font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Contractor Profile
        </h3>
        <div className="space-y-2 text-sm">
          <div className="flex justify-between">
            <span style={{ color: "var(--color-text-secondary)" }}>Registration</span>
            <span
              className="font-mono"
              style={{ color: "var(--color-text-primary)" }}
            >
              {data.registration_number}
            </span>
          </div>
          <div className="flex justify-between">
            <span style={{ color: "var(--color-text-secondary)" }}>Classification</span>
            <span
              className="font-mono"
              style={{ color: "var(--color-text-primary)" }}
            >
              {data.classification}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="stat-card">
          <div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
            Contracts
          </div>
          <div
            className="mt-1 font-mono text-xl font-bold"
            style={{ color: "var(--color-text-primary)" }}
          >
            {data.total_contracts}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
            Total Value
          </div>
          <div
            className="mt-1 font-mono text-xl font-bold"
            style={{ color: "var(--color-text-primary)" }}
          >
            {formatCompact(data.total_value)}
          </div>
        </div>
        <div className="stat-card">
          <div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
            Win Rate
          </div>
          <div
            className="mt-1 font-mono text-xl font-bold"
            style={{ color: "var(--color-text-primary)" }}
          >
            {(data.win_rate * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      <div>
        <h4
          className="mb-3 text-sm font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Agencies Served
        </h4>
        <div className="space-y-2">
          {data.agencies.slice(0, 5).map((agency) => (
            <div key={agency.id} className="flex items-center justify-between text-xs">
              <span
                className="truncate"
                style={{ color: "var(--color-text-secondary)" }}
              >
                {agency.name}
              </span>
              <div className="ml-2 flex flex-shrink-0 items-center gap-2">
                <span
                  className="font-mono"
                  style={{ color: "var(--color-text-secondary)" }}
                >
                  {agency.contract_count}
                </span>
                <span
                  className="font-mono"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {formatCompact(agency.total_value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {data.co_bidders.length > 0 && (
        <div>
          <h4
            className="mb-3 text-sm font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Frequent Co-Bidders
          </h4>
          <div className="space-y-2">
            {data.co_bidders.slice(0, 5).map((cobidder) => (
              <div key={cobidder.id} className="flex items-center justify-between text-xs">
                <span
                  className="truncate"
                  style={{ color: "var(--color-text-secondary)" }}
                >
                  {cobidder.name}
                </span>
                <div className="ml-2 flex flex-shrink-0 items-center gap-2">
                  <span
                    className="font-mono"
                    style={{ color: "var(--color-text-secondary)" }}
                  >
                    {cobidder.co_bid_count} co-bids
                  </span>
                  <span
                    className="rounded-full px-2 py-0.5"
                    style={{
                      backgroundColor: "var(--cobidder-badge-bg)",
                      color: "var(--cobidder-badge-text)",
                    }}
                  >
                    {cobidder.win_pattern}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.red_flags.length > 0 && (
        <div>
          <h4
            className="mb-3 text-sm font-semibold"
            style={{ color: "var(--color-text-primary)" }}
          >
            Red Flags
          </h4>
          <div className="space-y-2">
            {data.red_flags.map((flag, idx) => (
              <RedFlagBadge key={idx} redFlag={flag} compact />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
