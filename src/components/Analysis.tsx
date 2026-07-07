import type { TemporalData, SignalsData, PredictedTies, GraphData, Overlay, InNews, TemporalAnalysis as TAData } from "@/lib/types";
import { peso } from "@/lib/format";
import GraphTimeline from "@/components/graph/GraphTimeline";
import TemporalAnalysis from "@/components/TemporalAnalysis";

// Server-rendered network-analysis section: how the flood-control network
// formed year by year, the structural patterns in the record, and the
// Node2Vec predicted ties. Every number here is computed offline by
// scripts/build_analytics.py and interpolated; nothing is hand-written.

interface Props {
  temporal: TemporalData;
  signals: SignalsData;
  predicted: PredictedTies;
  graph: GraphData;
  overlay: Overlay;
  inNews: InNews;
  temporalAnalysis: TAData;
}

const W = 260;
const H = 110;
const PAD = { t: 14, r: 8, b: 18, l: 8 };

function scale(years: number[], vals: number[]) {
  const x = (i: number) =>
    PAD.l + (i / Math.max(1, years.length - 1)) * (W - PAD.l - PAD.r);
  const max = Math.max(...vals, 1e-9);
  const y = (v: number) => H - PAD.b - (v / max) * (H - PAD.t - PAD.b);
  return { x, y, max };
}

function LineChart({
  years, vals, color, fmt, title, note,
}: {
  years: number[]; vals: number[]; color: string;
  fmt: (v: number) => string; title: string; note: string;
}) {
  const { x, y } = scale(years, vals);
  const d = vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const last = vals.length - 1;
  return (
    <figure className="min-w-0">
      <figcaption className="text-[13px] font-semibold text-text-primary">{title}</figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-1 w-full" role="img" aria-label={`${title}, ${years[0]} to ${years[last]}`}>
        <line x1={PAD.l} y1={H - PAD.b} x2={W - PAD.r} y2={H - PAD.b} stroke="var(--hairline)" strokeWidth="1" />
        <path d={d} fill="none" stroke={color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
        <circle cx={x(0)} cy={y(vals[0])} r="2.5" fill={color} />
        <circle cx={x(last)} cy={y(vals[last])} r="2.5" fill={color} />
        <text x={x(0)} y={y(vals[0]) - 6} fontSize="10" fill="var(--text-secondary)" textAnchor="start" className="tabular">{fmt(vals[0])}</text>
        <text x={x(last)} y={y(vals[last]) - 6} fontSize="10" fill="var(--text-secondary)" textAnchor="end" className="tabular">{fmt(vals[last])}</text>
        <text x={PAD.l} y={H - 6} fontSize="9" fill="var(--text-muted)">{years[0]}</text>
        <text x={W - PAD.r} y={H - 6} fontSize="9" fill="var(--text-muted)" textAnchor="end">{years[last]}</text>
      </svg>
      <p className="mt-1 text-[11px] leading-snug text-text-muted">{note}</p>
    </figure>
  );
}

function BarChart({
  years, vals, color, fmt, title, note,
}: {
  years: number[]; vals: number[]; color: string;
  fmt: (v: number) => string; title: string; note: string;
}) {
  const { y } = scale(years, vals);
  const bw = (W - PAD.l - PAD.r) / years.length - 3;
  const peak = vals.indexOf(Math.max(...vals));
  return (
    <figure className="min-w-0">
      <figcaption className="text-[13px] font-semibold text-text-primary">{title}</figcaption>
      <svg viewBox={`0 0 ${W} ${H}`} className="mt-1 w-full" role="img" aria-label={`${title}, ${years[0]} to ${years[years.length - 1]}`}>
        <line x1={PAD.l} y1={H - PAD.b} x2={W - PAD.r} y2={H - PAD.b} stroke="var(--hairline)" strokeWidth="1" />
        {vals.map((v, i) => {
          const bx = PAD.l + i * ((W - PAD.l - PAD.r) / years.length) + 1.5;
          return <rect key={i} x={bx} y={y(v)} width={bw} height={H - PAD.b - y(v)} rx="1.5" fill={color} opacity={i === peak ? 1 : 0.55} />;
        })}
        <text
          x={PAD.l + peak * ((W - PAD.l - PAD.r) / years.length) + bw / 2}
          y={y(vals[peak]) - 5} fontSize="10" fill="var(--text-secondary)"
          textAnchor={peak > years.length - 3 ? "end" : "middle"} className="tabular"
        >
          {fmt(vals[peak])} ({years[peak]})
        </text>
        <text x={PAD.l} y={H - 6} fontSize="9" fill="var(--text-muted)">{years[0]}</text>
        <text x={W - PAD.r} y={H - 6} fontSize="9" fill="var(--text-muted)" textAnchor="end">{years[years.length - 1]}</text>
      </svg>
      <p className="mt-1 text-[11px] leading-snug text-text-muted">{note}</p>
    </figure>
  );
}

export default function Analysis({ temporal, signals, predicted, graph, overlay, inNews, temporalAnalysis }: Props) {
  const ys = temporal.years;
  const years = ys.map((y) => y.year);
  const first = ys[0];
  const last = ys[ys.length - 1];
  const peak = ys.reduce((a, b) => (b.fc_value > a.fc_value ? b : a), ys[0]);
  // 2016 is the observation start (every firm is "new"), so the entrant
  // series is shown and summarised from 2017 on.
  const entrantYs = ys.filter((y) => y.year >= 2017);
  const namedPeak = ys.reduce((a, b) => (b.named_share_pct > a.named_share_pct ? b : a), ys[0]);

  return (
    <section id="analysis" className="scroll-mt-20">
      <div className="mb-6">
        <p className="eyebrow">Network analysis, computed from the record</p>
        <h2 className="mt-1 font-display text-2xl font-bold text-text-primary md:text-3xl">
          How the network formed
        </h2>
        <p className="mt-2 max-w-2xl text-sm text-text-secondary">
          Year by year, {first.year} to {last.year}: the money grew, the named firms&apos; share of it grew,
          the market closed to newcomers, and the joint-venture web consolidated. Every figure below is
          computed from the contract record. {temporal._meta.disclaimer}
        </p>
      </div>

      {/* The replay: the actual network forming, not a trend line. */}
      <div className="mb-10">
        <GraphTimeline data={graph} overlay={overlay} inNews={inNews} />
      </div>

      {/* Small multiples: one job per chart, no dual axes. */}
      <div className="grid grid-cols-1 gap-x-8 gap-y-6 sm:grid-cols-2 lg:grid-cols-4">
        <BarChart
          years={years}
          vals={ys.map((y) => y.fc_value)}
          color="var(--accent)"
          fmt={(v) => peso(v)}
          title="Flood-control value per year"
          note={`From ${peso(first.fc_value)} (${first.year}) to a ${peso(peak.fc_value)} peak (${peak.year}).`}
        />
        <LineChart
          years={years}
          vals={ys.map((y) => y.named_share_pct)}
          color="var(--signal)"
          fmt={(v) => `${v.toFixed(1)}%`}
          title="The 16 named firms' share"
          note={`Share of each year's flood-control value won by the firms later named in the inquiry: ${first.named_share_pct.toFixed(1)}% to a ${namedPeak.named_share_pct.toFixed(1)}% peak (${namedPeak.year}).`}
        />
        <LineChart
          years={entrantYs.map((y) => y.year)}
          vals={entrantYs.map((y) => y.entrant_share_pct)}
          color="var(--alert)"
          fmt={(v) => `${v.toFixed(1)}%`}
          title="Newcomers' share of the money"
          note={`Value share of firms winning flood control for the first time. The market closed as spending tripled. (2016 is the observation start and is excluded.)`}
        />
        <LineChart
          years={years}
          vals={ys.map((y) => y.jv_giant_component)}
          color="var(--water)"
          fmt={(v) => v.toLocaleString()}
          title="The joint-venture web"
          note={`Firms in the largest connected group of the cumulative JV network: ${first.jv_giant_component} (${first.year}) to ${last.jv_giant_component.toLocaleString()} (${last.year}), one web.`}
        />
      </div>

      {/* Validated temporal-KG findings lead, before the descriptive indicators. */}
      <TemporalAnalysis data={temporalAnalysis} />

      {/* Structural patterns */}
      <div className="mt-12">
        <h3 className="font-display text-lg font-bold text-text-primary">Patterns in the record</h3>
        <p className="mt-1.5 max-w-3xl text-[13px] leading-relaxed text-text-muted">{signals._meta.framing}</p>
        <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-2">
          <SignalCard
            title="Near-identical bidding footprints"
            count={signals.footprint_pairs.count}
            definition={signals.footprint_pairs.definition}
          >
            <ul className="space-y-1.5">
              {signals.footprint_pairs.items.slice(0, 5).map((it, i) => (
                <li key={i} className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="min-w-0 truncate text-text-secondary">{it.firms[0]} + {it.firms[1]}</span>
                  <span className="tabular shrink-0 text-text-muted">{it.shared_offices} offices · J {it.jaccard}</span>
                </li>
              ))}
            </ul>
          </SignalCard>
          <SignalCard
            title="Joint-venture rings"
            count={signals.jv_groups.count}
            definition={signals.jv_groups.definition}
          >
            <ul className="space-y-1.5">
              {signals.jv_groups.items.slice(0, 4).map((it, i) => (
                <li key={i} className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="min-w-0 truncate text-text-secondary">{it.firms.slice(0, 3).join(", ")}{it.size > 3 ? ` +${it.size - 3}` : ""}</span>
                  <span className="tabular shrink-0 text-text-muted">{it.size} firms · {peso(it.combined_fc_value)}</span>
                </li>
              ))}
            </ul>
          </SignalCard>
          <SignalCard
            title="Alternating top awardees"
            count={signals.alternation.count}
            definition={signals.alternation.definition}
          >
            {signals.alternation.count === 0 ? (
              <p className="text-[13px] text-text-secondary">
                None met the threshold. Reported as tested: concentration here shows up as one dominant firm
                per office, not two firms trading the top spot.
              </p>
            ) : (
              <ul className="space-y-1.5">
                {signals.alternation.items.slice(0, 4).map((it, i) => (
                  <li key={i} className="text-[13px] text-text-secondary">
                    {it.office}: {it.firms.join(" and ")} ({it.switches} switches)
                  </li>
                ))}
              </ul>
            )}
          </SignalCard>
          <SignalCard
            title="New firms, immediate large awards"
            count={signals.entrants.count}
            definition={signals.entrants.definition}
          >
            <ul className="space-y-1.5">
              {signals.entrants.items.slice(0, 5).map((it, i) => (
                <li key={i} className="flex items-baseline justify-between gap-3 text-[13px]">
                  <span className="min-w-0 truncate text-text-secondary">{it.firm}</span>
                  <span className="tabular shrink-0 text-text-muted">{it.first_year} · {peso(it.value_first_two_years)} in 2 yrs</span>
                </li>
              ))}
            </ul>
          </SignalCard>
        </div>
      </div>

      {/* Predicted ties */}
      <div className="mt-12">
        <h3 className="font-display text-lg font-bold text-text-primary">Predicted ties (statistical, unverified)</h3>
        <p className="mt-1.5 max-w-3xl text-[13px] leading-relaxed text-text-muted">{predicted._meta.method}</p>
        <div className="mt-4 overflow-x-auto rounded-xl border border-hairline">
          <table className="w-full border-collapse text-sm">
            <thead>
              <tr className="border-b border-hairline text-left text-[11px] uppercase tracking-wide text-text-muted">
                <th className="px-3 py-2">Firm pair (no recorded joint venture)</th>
                <th className="px-3 py-2 text-right" title="Node2Vec cosine similarity">Score</th>
                <th className="px-3 py-2 text-right" title="Shared district offices">Offices</th>
                <th className="px-3 py-2 text-right" title="Adamic-Adar index">A-A</th>
              </tr>
            </thead>
            <tbody>
              {predicted.pairs.slice(0, 10).map((p, i) => (
                <tr key={i} className="border-b border-hairline/60 last:border-b-0">
                  <td className="px-3 py-1.5 text-text-secondary">{p.firms[0]} + {p.firms[1]}</td>
                  <td className="tabular px-3 py-1.5 text-right text-text-secondary">{p.score.toFixed(3)}</td>
                  <td className="tabular px-3 py-1.5 text-right text-text-muted">{p.shared_offices}</td>
                  <td className="tabular px-3 py-1.5 text-right text-text-muted">{p.adamic_adar.toFixed(2)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="mt-3 max-w-3xl text-[12px] leading-relaxed text-text-muted">
          {predicted._meta.caveat} In the explorer, these render as the faintest tier and are off until
          switched on in the legend.
        </p>
      </div>
    </section>
  );
}

function SignalCard({ title, count, definition, children }: {
  title: string; count: number; definition: string; children: React.ReactNode;
}) {
  return (
    <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
      <div className="mb-1 flex items-baseline justify-between gap-3">
        <h4 className="font-display text-[15px] font-semibold text-text-primary">{title}</h4>
        <span className="tabular text-sm text-text-muted">{count} found</span>
      </div>
      <p className="mb-3 text-[12px] leading-relaxed text-text-muted">{definition}</p>
      {children}
    </div>
  );
}
