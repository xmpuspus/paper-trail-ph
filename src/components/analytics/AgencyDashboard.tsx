"use client";

import { useEffect, useState } from "react";
import type { AgencyConcentration } from "@/types/api";
import { getAgencyConcentration } from "@/lib/api";
import { formatCompact } from "@/lib/constants";
import ConcentrationChart from "./ConcentrationChart";
import { Spinner } from "@/components/common/Loading";

interface AgencyDashboardProps {
  agencyId: string;
}

function getHHIInterpretation(hhi: number): { level: string; cssVar: string; description: string } {
  if (hhi >= 0.25) {
    return {
      level: "High Concentration",
      cssVar: "var(--badge-risk-high-text)",
      description: "Market highly concentrated, limited competition",
    };
  } else if (hhi >= 0.15) {
    return {
      level: "Moderate Concentration",
      cssVar: "var(--badge-risk-medium-text)",
      description: "Some concentration, monitor for competition issues",
    };
  } else {
    return {
      level: "Low Concentration",
      cssVar: "var(--badge-risk-low-text)",
      description: "Competitive market with multiple suppliers",
    };
  }
}

export default function AgencyDashboard({ agencyId }: AgencyDashboardProps) {
  const [data, setData] = useState<AgencyConcentration | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const result = await getAgencyConcentration(agencyId);
        setData(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load agency data");
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [agencyId]);

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

  const hhiInterpretation = getHHIInterpretation(data.hhi);

  return (
    <div className="space-y-6 p-4">
      <div>
        <h3
          className="mb-4 text-lg font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Agency Overview
        </h3>
        <div className="grid grid-cols-2 gap-4">
          <div className="stat-card">
            <div className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
              Total Contracts
            </div>
            <div
              className="mt-1 font-mono text-2xl font-bold"
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
              className="mt-1 font-mono text-2xl font-bold"
              style={{ color: "var(--color-text-primary)" }}
            >
              {formatCompact(data.total_value)}
            </div>
          </div>
        </div>
      </div>

      <div>
        <h4
          className="mb-2 text-sm font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Concentration Analysis
        </h4>
        <div className="stat-card">
          <div className="flex items-baseline justify-between">
            <span className="text-xs" style={{ color: "var(--color-text-secondary)" }}>
              HHI Score
            </span>
            <span
              className="font-mono text-xl font-bold"
              style={{ color: "var(--color-text-primary)" }}
            >
              {data.hhi.toFixed(3)}
            </span>
          </div>
          <div
            className="mt-2 text-sm font-semibold"
            style={{ color: hhiInterpretation.cssVar }}
          >
            {hhiInterpretation.level}
          </div>
          <div
            className="mt-1 text-xs"
            style={{ color: "var(--color-text-secondary)" }}
          >
            {hhiInterpretation.description}
          </div>
        </div>
      </div>

      <div>
        <h4
          className="mb-3 text-sm font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Top Contractors
        </h4>
        <ConcentrationChart
          data={data.top_contractors.map((c) => ({
            name: c.name,
            value: c.total_value,
            percentage: c.share * 100,
          }))}
          maxItems={5}
        />
      </div>

      <div>
        <h4
          className="mb-3 text-sm font-semibold"
          style={{ color: "var(--color-text-primary)" }}
        >
          Procurement Methods
        </h4>
        <div className="space-y-2">
          {data.procurement_methods.map((method, idx) => (
            <div key={idx} className="flex items-center justify-between text-xs">
              <span style={{ color: "var(--color-text-secondary)" }}>
                {method.method}
              </span>
              <div className="flex items-center gap-2">
                <span
                  className="font-mono"
                  style={{ color: "var(--color-text-secondary)" }}
                >
                  {method.count} contracts
                </span>
                <span
                  className="font-mono"
                  style={{ color: "var(--color-text-muted)" }}
                >
                  {formatCompact(method.total_value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
