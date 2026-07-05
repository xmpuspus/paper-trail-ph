import { ArrowRight, Graph } from "@phosphor-icons/react/dist/ssr";
import type { Stats } from "@/lib/types";
import { peso, num } from "@/lib/format";
import StatTiles from "@/components/graph/StatTiles";

export default function Hero({ stats }: { stats: Stats }) {
  const tiles = [
    { label: "Flood-control value", value: peso(stats.flood_control.value), sub: "2016–2026, recorded", tone: "signal" as const },
    { label: "Flood-control contracts", value: num(stats.flood_control.contracts), sub: "DPWH category" },
    { label: "Distinct firms", value: num(stats.totals.contractors), sub: `resolved from ${num(stats.totals.contracts)} contracts` },
    { label: "Concentrated offices", value: num(stats.concentration.concentrated_fc_deos), sub: "HHI > 2500" },
  ];

  return (
    <section className="pt-8 md:pt-12">
      <p className="eyebrow">Philippine public accountability graph</p>
      <h1 className="mt-3 max-w-4xl font-display text-4xl font-extrabold leading-[1.05] tracking-tight text-text-primary md:text-6xl">
        The flood-control money,
        <span className="text-accent"> mapped.</span>
      </h1>
      <p className="mt-5 max-w-2xl text-base leading-relaxed text-text-secondary md:text-lg">
        An interactive graph of every DPWH flood-control contract on the public record: {num(stats.flood_control.contracts)} projects
        worth {peso(stats.flood_control.value)}, the firms that won them, and the license revocations, blacklists, and court
        filings now attached to some of them. It shows statistical indicators, not verdicts.
      </p>

      <div className="mt-7 flex flex-wrap gap-3">
        <a href="#story" className="btn btn-primary">
          Walk the scandal <ArrowRight size={16} />
        </a>
        <a href="#explore" className="btn btn-ghost">
          <Graph size={16} /> Explore the graph
        </a>
      </div>

      <div className="waterline mt-9" />

      <div className="mt-6">
        <StatTiles tiles={tiles} />
      </div>

      <p className="mt-5 max-w-2xl text-xs leading-relaxed text-text-muted">
        Data sourced from public records (COA, SEC, DBM, PSA, BSP, SALN disclosures) and named court and agency filings.
        This tool computes statistical indicators only. Specific allegations, if any, require independent investigation and
        corroboration. Charges are allegations under the presumption of innocence.
      </p>
    </section>
  );
}
