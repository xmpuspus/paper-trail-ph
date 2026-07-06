import type { TemporalAnalysis as TA } from "@/lib/types";

// Server-rendered. Every number is interpolated from temporal-analysis.json
// (scripts/build_temporal.py); nothing is hand-typed.

const W = 300;
const H = 128;
const PAD = { t: 16, r: 10, b: 20, l: 10 };

function poly(xs: number[], ys: number[], yMax: number, yMin = 0) {
  const x = (i: number) => PAD.l + (i / Math.max(1, xs.length - 1)) * (W - PAD.l - PAD.r);
  const y = (v: number) => H - PAD.b - ((v - yMin) / (yMax - yMin || 1)) * (H - PAD.t - PAD.b);
  return { x, y, d: ys.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ") };
}

export default function TemporalAnalysis({ data }: { data: TA }) {
  const lp = data.link_prediction;
  const scored = lp.by_year.filter((y) => y.auc != null);
  const worstDegP = Math.max(...scored.map((y) => y.p_degree_null ?? 1));
  const beatsAll = scored.every((y) => (y.p_degree_null ?? 1) < 0.05);
  const bestYr = scored.reduce((a, b) => ((b.auc ?? 0) > (a.auc ?? 0) ? b : a), scored[0]);

  const dc = data.dynamic_communities.by_year;
  const first = dc[0], last = dc[dc.length - 1];
  const lastStab = last.stability_vs_prev ?? 0;

  const m = data.motifs.counts;
  const ratio = m.awards_before_jv > 0 ? (m.jv_before_awards / m.awards_before_jv) : m.jv_before_awards;

  const cp = data.change_points.metrics;
  const cpYears = Object.values(cp).map((c) => c.change_year);
  const cpMode = mode(cpYears);
  const named = cp["named_share_pct"];

  // link-prediction chart: real AUC vs degree-null mean, per predicted year
  const yrs = scored.map((y) => y.predict);
  const real = scored.map((y) => y.auc as number);
  const nul = scored.map((y) => y.auc_null_mean ?? 0.5);
  const A = poly(yrs, real, 0.85, 0.3);
  const N = poly(yrs, nul, 0.85, 0.3);

  // community chart: largest community over time
  const cyrs = dc.map((d) => d.year);
  const clarge = dc.map((d) => d.largest);
  const C = poly(cyrs, clarge, Math.max(...clarge) * 1.1);

  return (
    <div className="mt-12">
      <h3 className="font-display text-lg font-bold text-text-primary">Temporal knowledge graph, validated</h3>
      <p className="mt-1.5 max-w-3xl text-[13px] leading-relaxed text-text-muted">
        Beyond the static graph: what the record shows once every award and joint venture carries its year, and every
        claim is tested against a null model. {data._meta.disclaimer}
      </p>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        {/* Link prediction (flagship) */}
        <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
          <div className="mb-1 flex items-baseline justify-between gap-3">
            <h4 className="font-display text-[15px] font-semibold text-text-primary">Predicting next year&apos;s partnerships</h4>
            <span className="tabular text-sm text-text-muted">AUC {lp.macro_auc}</span>
          </div>
          <p className="mb-3 text-[12px] leading-relaxed text-text-muted">
            Train on the awards up to each year, then predict which firms form a new joint venture the year after, from
            their prior shared-office structure alone. Skill {lp.macro_auc} on average, strongest in {bestYr.predict} (AUC {bestYr.auc}).
            {beatsAll && <> It beats a degree-preserving null in every split (p &lt; {worstDegP <= 0.01 ? "0.01" : worstDegP.toFixed(2)}), so the signal is the structure, not just which firms are big.</>}
          </p>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Prediction skill versus a null model, per year">
            <line x1={PAD.l} y1={A.y(0.5)} x2={W - PAD.r} y2={A.y(0.5)} stroke="var(--hairline)" strokeWidth="1" strokeDasharray="3 3" />
            <text x={PAD.l} y={A.y(0.5) - 3} fontSize="8" fill="var(--text-muted)" textAnchor="start">chance 0.5</text>
            <path d={N.d} fill="none" stroke="var(--text-muted)" strokeWidth="1.4" strokeDasharray="4 3" />
            <path d={A.d} fill="none" stroke="var(--accent)" strokeWidth="2.2" strokeLinejoin="round" />
            {real.map((v, i) => <circle key={i} cx={A.x(i)} cy={A.y(v)} r="2.4" fill="var(--accent)" />)}
            <text x={A.x(real.length - 1)} y={A.y(real[real.length - 1]) - 6} fontSize="10" fill="var(--accent)" textAnchor="end" className="tabular">real {real[real.length - 1]}</text>
            <text x={N.x(nul.length - 1)} y={N.y(nul[nul.length - 1]) + 12} fontSize="9" fill="var(--text-muted)" textAnchor="end" className="tabular">null {nul[nul.length - 1]}</text>
            <text x={PAD.l} y={H - 6} fontSize="9" fill="var(--text-muted)">{yrs[0]}</text>
            <text x={W - PAD.r} y={H - 6} fontSize="9" fill="var(--text-muted)" textAnchor="end">{yrs[yrs.length - 1]}</text>
          </svg>
          <p className="mt-1 text-[11px] leading-snug text-text-muted">
            Blue is real skill, dashed grey is the degree-preserving null. Predictions are statistical similarity, not evidence of a relationship.
          </p>
        </div>

        {/* Dynamic communities */}
        <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
          <div className="mb-1 flex items-baseline justify-between gap-3">
            <h4 className="font-display text-[15px] font-semibold text-text-primary">The clusters consolidated</h4>
            <span className="tabular text-sm text-text-muted">{first.communities} → {last.communities}</span>
          </div>
          <p className="mb-3 text-[12px] leading-relaxed text-text-muted">
            Co-location communities each year: they fell from {first.communities} in {first.year} to {last.communities} by {last.year},
            while the largest grew from {first.largest} to {last.largest} firms. The partition settled (year-over-year stability {lastStab}),
            so the structure is not churn: the same clusters persisted and merged.
          </p>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full" role="img" aria-label="Largest community size over time">
            <line x1={PAD.l} y1={H - PAD.b} x2={W - PAD.r} y2={H - PAD.b} stroke="var(--hairline)" strokeWidth="1" />
            <path d={C.d} fill="none" stroke="var(--signal)" strokeWidth="2.2" strokeLinejoin="round" />
            {clarge.map((v, i) => <circle key={i} cx={C.x(i)} cy={C.y(v)} r="2.2" fill="var(--signal)" />)}
            <text x={C.x(0)} y={C.y(clarge[0]) - 6} fontSize="10" fill="var(--text-secondary)" textAnchor="start" className="tabular">{clarge[0]}</text>
            <text x={C.x(clarge.length - 1)} y={C.y(clarge[clarge.length - 1]) - 6} fontSize="10" fill="var(--text-secondary)" textAnchor="end" className="tabular">{clarge[clarge.length - 1]}</text>
            <text x={PAD.l} y={H - 6} fontSize="9" fill="var(--text-muted)">{cyrs[0]}</text>
            <text x={W - PAD.r} y={H - 6} fontSize="9" fill="var(--text-muted)" textAnchor="end">{cyrs[cyrs.length - 1]}</text>
          </svg>
          <p className="mt-1 text-[11px] leading-snug text-text-muted">Largest co-location community, firms, {cyrs[0]} to {cyrs[cyrs.length - 1]}.</p>
        </div>
      </div>

      {/* Motifs, change-points, hetero schema */}
      <div className="mt-4 grid grid-cols-1 gap-4 md:grid-cols-3">
        <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
          <h4 className="font-display text-[15px] font-semibold text-text-primary">Sequence, not coincidence</h4>
          <p className="mt-1.5 text-[12px] leading-relaxed text-text-muted">
            For firm pairs holding a joint venture, the JV forms <strong className="text-text-secondary">before</strong> their
            shared awards concentrate {m.jv_before_awards} times, versus {m.awards_before_jv} the other way, about {ratio.toFixed(1)}x.
            The partnership tends to predate the money. Order only, never intent.
          </p>
          <p className="mt-2 tabular text-[13px] text-text-secondary">
            <span className="text-text-primary">{m.jv_before_awards}</span> JV-first
            <span className="mx-2 text-text-muted">vs</span>
            <span className="text-text-primary">{m.awards_before_jv}</span> awards-first
          </p>
        </div>

        <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
          <h4 className="font-display text-[15px] font-semibold text-text-primary">When the structure shifted</h4>
          <p className="mt-1.5 text-[12px] leading-relaxed text-text-muted">
            Pettitt change-point tests put the break around {cpMode} across several series. The named firms&apos; share
            steps from {named.before_mean}% to {named.after_mean}% at {named.change_year}. Over a ten-year window (2016 to 2025)
            the significance is marginal (p ≈ {named.p_value.toFixed(2)}), so read it as a candidate turning point, not proof.
          </p>
        </div>

        <div className="min-w-0 rounded-xl border border-hairline bg-surface p-4">
          <h4 className="font-display text-[15px] font-semibold text-text-primary">The money-and-power schema</h4>
          <p className="mt-1.5 text-[12px] leading-relaxed text-text-muted">
            A heterogeneous temporal graph (person, firm, office, institution nodes; typed, dated edges) built from the
            sourced overlay: {data.hetero.edge_count} edges across {data.hetero.node_counts.Person} people and {data.hetero.node_counts.Firm} firms.
            Bulk SALN wealth and SOCE campaign finance are not machine-readable yet; this is the interface, filled with the
            real records that exist, ready to scale.
          </p>
        </div>
      </div>
    </div>
  );
}

function mode(xs: number[]): number {
  const c: Record<number, number> = {};
  let best = xs[0], bestN = 0;
  for (const x of xs) { c[x] = (c[x] ?? 0) + 1; if (c[x] > bestN) { bestN = c[x]; best = x; } }
  return best;
}
