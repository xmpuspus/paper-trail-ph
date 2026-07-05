import { ArrowRight } from "@phosphor-icons/react/dist/ssr";
import type { Stats } from "@/lib/types";
import { peso, num } from "@/lib/format";

export default function Hero({ stats }: { stats: Stats }) {
  const figures = [
    { value: peso(stats.flood_control.value), label: "in flood-control contracts", sub: "2016 to 2026, recorded", tone: "var(--signal)" },
    { value: num(stats.flood_control.contracts), label: "flood-control projects", sub: "DPWH category" },
    { value: num(stats.totals.contractors), label: "distinct firms", sub: `resolved from ${num(stats.totals.contracts)} contracts` },
    { value: num(stats.concentration.concentrated_fc_deos), label: "concentrated offices", sub: "one or two firms dominate" },
  ];

  return (
    <section className="pt-14 md:pt-24">
      <p className="eyebrow">Philippine public accountability</p>
      <h1 className="mt-4 max-w-3xl text-[38px] font-extrabold leading-[1.05] tracking-tight text-text-primary md:text-[64px]">
        The flood-control money, mapped.
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-relaxed text-text-secondary md:text-xl">
        Every DPWH flood-control contract on the public record, the firms that won them, and the
        license revocations, blacklists, and court filings now attached to some. It shows statistical
        indicators, not verdicts.
      </p>

      <div className="mt-9 flex flex-wrap gap-3">
        <a href="#story" className="btn btn-primary">
          Walk the paper trail <ArrowRight size={17} />
        </a>
        <a href="#explore" className="btn btn-ghost">Explore the graph</a>
      </div>

      <dl className="mt-16 grid grid-cols-2 gap-x-8 gap-y-10 border-t border-hairline pt-10 md:grid-cols-4">
        {figures.map((f) => (
          <div key={f.label}>
            <dd className="figure text-[32px] md:text-[40px]" style={{ color: f.tone ?? "var(--text-primary)" }}>{f.value}</dd>
            <dt className="mt-2 text-[15px] text-text-secondary">{f.label}</dt>
            <dd className="mt-0.5 text-[13px] text-text-muted">{f.sub}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-8 max-w-3xl text-[13px] leading-relaxed text-text-muted">
        Data from public records (DPWH Transparency Portal via BetterGov.PH, CC0). This tool computes
        statistical indicators only. Charges are allegations under the presumption of innocence, and
        each links to its source.
      </p>
    </section>
  );
}
