"use client";

import { X, ArrowSquareOut, Info } from "@phosphor-icons/react";
import type { Entity, Overlay, InNews, OverlayPerson, PredictedTies, SecData } from "@/lib/types";
import { ACTION_META } from "@/lib/tiers";
import { peso, pesoFull, num, shortDate } from "@/lib/format";

const TONE: Record<string, { chip: string; border: string }> = {
  action: { chip: "chip-signal", border: "border-signal/40" },
  alleged: { chip: "chip-alert", border: "border-alert/40" },
  note: { chip: "chip", border: "border-hairline" },
  cleared: { chip: "chip-good", border: "border-good/40" },
};

interface Props {
  entity: Entity | null;
  overlay: Overlay | null;
  inNews: InNews | null;
  predicted?: PredictedTies | null;
  sec?: SecData | null;
  resolveName?: (key: string) => string | undefined;
  onClose: () => void;
  onSelectRelated: (key: string) => void;
}

export default function EntityDetail({ entity, overlay, inNews, predicted, sec, resolveName, onClose, onSelectRelated }: Props) {
  if (!entity) return null;
  const isFirm = entity.type === "Contractor";
  const isPerson = entity.type === "Person";
  const ov = isFirm ? overlay?.firms?.[entity.key] : undefined;
  const ovOffice = entity.type === "ProcuringEntity" ? overlay?.offices?.[entity.key] : undefined;
  const secFirm = isFirm ? sec?.firms?.[entity.key] : undefined;
  const news = isFirm ? inNews?.firms?.[entity.key] : undefined;
  const persons: OverlayPerson[] =
    isFirm && overlay ? overlay.persons.filter((p) => p.firms.includes(entity.key)) : [];
  const source = (k: string) => overlay?.sources?.[k];
  const predictedForFirm = isFirm
    ? (predicted?.pairs ?? []).filter((p) => p.keys.includes(entity.key))
    : [];

  return (
    <aside
      className="flex h-full w-full flex-col overflow-hidden panel"
      aria-label={`Details for ${entity.label}`}
    >
      <header className="flex items-start justify-between gap-3 border-b border-hairline p-4">
        <div className="min-w-0">
          <p className="eyebrow mb-1">{isPerson ? "Person on the record" : isFirm ? "Contractor" : "Procuring entity · DPWH district office"}</p>
          <h2 className="font-display text-[19px] font-bold leading-tight text-text-primary">{entity.label}</h2>
          {entity.former && (
            <p className="mt-1 text-xs text-text-muted">Formerly: {entity.former}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-1.5">
            {entity.revoked && <span className="chip chip-signal">DPWH license recorded as revoked</span>}
            {secFirm && <span className="chip">SEC on record</span>}
            {news && <span className="chip chip-water">In the news</span>}
            {entity.concentrated && <span className="chip chip-signal">Concentrated market (HHI &gt; 2500)</span>}
          </div>
        </div>
        <button onClick={onClose} className="btn-ghost grid h-10 w-10 shrink-0 place-items-center" aria-label="Close details">
          <X size={18} />
        </button>
      </header>

      <div className="custom-scrollbar flex-1 overflow-y-auto p-4">
        {/* Person: curated, source-linked role and status; no contract records */}
        {isPerson && (
          <>
            <Section title="On the record">
              {entity.role && <p className="text-sm leading-relaxed text-text-secondary">{entity.role}</p>}
              {entity.status && <p className="mt-2 text-sm leading-relaxed text-text-secondary">{entity.status}</p>}
              <div className="mt-2 flex flex-wrap gap-2">
                {(entity.sources ?? []).map((sk) => {
                  const s = source(sk);
                  return s ? (
                    <a key={sk} href={s.url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1 text-xs">
                      {s.label} <ArrowSquareOut size={11} />
                    </a>
                  ) : null;
                })}
              </div>
              <p className="mt-3 flex items-start gap-1.5 text-[11px] leading-relaxed text-text-muted">
                <Info size={13} className="mt-0.5 shrink-0" />
                Charges and flags are allegations under the presumption of innocence. Every item above links to its source.
              </p>
            </Section>
            {(entity.firms ?? []).length > 0 && (
              <Section title="Linked firms (on the record)">
                <ul className="flex flex-wrap gap-1.5">
                  {(entity.firms ?? []).map((fk) => (
                    <li key={fk}>
                      <button onClick={() => onSelectRelated(fk)} className="chip hover:border-accent">
                        {resolveName?.(fk) ?? fk}
                      </button>
                    </li>
                  ))}
                </ul>
              </Section>
            )}
          </>
        )}

        {/* Recorded facts from the DPWH dataset */}
        {!isPerson && (
        <Section title="What the records show">
          <dl className="grid grid-cols-2 gap-3">
            <Metric label="DPWH contracts" value={num(entity.n_contracts)} />
            <Metric label="Total contract value" value={peso(entity.value)} title={pesoFull(entity.value)} />
            <Metric label="Flood-control contracts" value={num(entity.fc_contracts)} />
            <Metric label="Flood-control value" value={peso(entity.fc_value)} title={pesoFull(entity.fc_value)} tone="signal" />
            {isFirm ? (
              <>
                <Metric label="District offices" value={num(entity.n_deos)} />
                <Metric label="Regions" value={num(entity.n_regions)} />
              </>
            ) : (
              <>
                <Metric label="Region" value={entity.region ?? "—"} />
                <Metric label="Flood-control HHI" value={entity.hhi_fc ? Math.round(entity.hhi_fc).toString() : "—"} tone={entity.concentrated ? "signal" : undefined} />
                <Metric label="Firms (flood control)" value={num(entity.n_fc_firms)} />
              </>
            )}
          </dl>
          <p className="mt-3 text-[11px] leading-relaxed text-text-muted">
            Value is the sum of contract budgets where this{" "}
            {isFirm ? "firm is the sole or a joint awardee" : "district office is the procuring entity"}, 2016–2026.
            Descriptive statistics from public records. Patterns may have legitimate explanations.
          </p>
        </Section>
        )}

        {/* Procuring office: curated, source-linked findings (COA fraud audits) */}
        {ovOffice && ovOffice.actions.length > 0 && (
          <Section title="On the record">
            <ul className="space-y-3">
              {ovOffice.actions.map((a, i) => {
                const meta = ACTION_META[a.type];
                const src = source(a.source);
                const t = TONE[meta?.tone ?? "note"];
                return (
                  <li key={i} className={`rounded-lg border p-3 ${t.border}`}>
                    <div className="mb-1 flex items-center gap-2">
                      <span className={`chip ${t.chip}`}>{meta?.label ?? a.type}</span>
                      <span className="text-[11px] text-text-muted">{shortDate(a.date)}</span>
                    </div>
                    <p className="text-sm leading-relaxed text-text-secondary">{a.label}</p>
                    {src && (
                      <a href={src.url} target="_blank" rel="noopener noreferrer" className="link-source mt-1.5 inline-flex items-center gap-1 text-xs">
                        {src.label} <ArrowSquareOut size={12} />
                      </a>
                    )}
                  </li>
                );
              })}
            </ul>
            <p className="mt-3 flex items-start gap-1.5 text-[11px] leading-relaxed text-text-muted">
              <Info size={13} className="mt-0.5 shrink-0" />
              Audit findings are allegations under the presumption of innocence. Cases are pending unless a court has ruled otherwise.
            </p>
          </Section>
        )}

        {/* Corporate registry (SEC): primary-document facts, recorded tier */}
        {isFirm && secFirm && (
          <Section
            title="Corporate registry (SEC)"
            hint="From the firm's own General Information Sheet, published by PCIJ. A recorded fact, not a scrape."
          >
            <dl className="grid grid-cols-2 gap-3">
              <Metric label="SEC registration" value={secFirm.sec_reg_no} sub={`registered ${secFirm.reg_year}`} />
              <Metric
                label="Paid-up capital"
                value={secFirm.paid_up_capital != null ? pesoFull(secFirm.paid_up_capital) : "—"}
                title={secFirm.paid_up_capital != null ? pesoFull(secFirm.paid_up_capital) : undefined}
              />
              {secFirm.contract_to_capital != null && (
                <Metric
                  label="Flood-control value : capital"
                  value={`${secFirm.contract_to_capital.toLocaleString()}x`}
                  tone="signal"
                />
              )}
              <Metric label="Registered office" value={secFirm.registered_office} sub={secFirm.region} />
            </dl>
            {secFirm.contract_to_capital != null && (
              <p className="mt-2 text-[11px] leading-relaxed text-text-muted">
                {peso(secFirm.fc_value)} in flood-control contract value on the DPWH record against{" "}
                {pesoFull(secFirm.paid_up_capital as number)} paid-up capital on the 2025 GIS. A statistical
                indicator, not evidence of wrongdoing.
              </p>
            )}
            {secFirm.capital_note && (
              <p className="mt-2 text-[11px] leading-relaxed text-text-muted">{secFirm.capital_note}</p>
            )}
            {(secFirm.president || secFirm.family_control) && (
              <p className="mt-2 text-[12px] leading-relaxed text-text-secondary">
                {secFirm.president && <><span className="text-text-muted">President: </span>{secFirm.president}. </>}
                {secFirm.family_control}
              </p>
            )}
            {secFirm.officer_note && (
              <p className="mt-2 text-[12px] leading-relaxed text-text-secondary">{secFirm.officer_note}</p>
            )}
            {secFirm.re_registration && (
              <div className="mt-3 rounded-lg border border-signal/40 p-3">
                <div className="mb-1 flex items-center gap-2">
                  <span className="chip chip-signal">Re-registration flag</span>
                </div>
                <p className="text-sm leading-relaxed text-text-secondary">{secFirm.re_registration.label}</p>
                {source(secFirm.re_registration.source) && (
                  <a
                    href={source(secFirm.re_registration.source)!.url}
                    target="_blank" rel="noopener noreferrer"
                    className="link-source mt-1.5 inline-flex items-center gap-1 text-xs"
                  >
                    {source(secFirm.re_registration.source)!.label} <ArrowSquareOut size={12} />
                  </a>
                )}
              </div>
            )}
            <div className="mt-3 flex flex-wrap gap-2">
              {secFirm.gis_url && (
                <a href={secFirm.gis_url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1 text-xs">
                  SEC GIS (PCIJ) <ArrowSquareOut size={11} />
                </a>
              )}
              {secFirm.aoi_url && (
                <a href={secFirm.aoi_url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1 text-xs">
                  Articles of Incorporation <ArrowSquareOut size={11} />
                </a>
              )}
            </div>
          </Section>
        )}

        {/* Recorded footprint: where the money went */}
        {isFirm && entity.top_deos && entity.top_deos.length > 0 && (
          <Section title="Recorded footprint" hint="Where this firm's flood-control contracts were procured.">
            <ul className="space-y-1.5">
              {entity.top_deos.filter((d) => (d.fc_contracts ?? 0) > 0).slice(0, 6).map((d) => (
                <li key={d.deo} className="flex items-baseline justify-between gap-3 text-sm">
                  <span className="min-w-0 truncate text-text-secondary">{d.deo}</span>
                  <span className="tabular shrink-0 text-text-muted">
                    {num(d.fc_contracts)} · {peso(d.fc_value)}
                  </span>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Recorded joint ventures (solid-tier edges) */}
        {isFirm && entity.coawardees && entity.coawardees.filter((c) => c.fc_shared > 0).length > 0 && (
          <Section title="Joint awardees (recorded)" hint="Firms that jointly won contracts with this one. A recorded relationship, solid line in the graph.">
            <ul className="flex flex-wrap gap-1.5">
              {entity.coawardees.filter((c) => c.fc_shared > 0).slice(0, 12).map((c) => (
                <li key={c.key}>
                  <button
                    onClick={() => onSelectRelated(c.key)}
                    className="chip hover:border-accent"
                    title={`${c.shared} shared contracts`}
                  >
                    {c.name} <span className="tabular text-text-muted">· {c.fc_shared}</span>
                  </button>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* Node2Vec predicted ties: the faintest tier, statistical only */}
        {predictedForFirm.length > 0 && (
          <Section
            title="Predicted ties (statistical, unverified)"
            hint="Node2Vec similarity in bidding footprint with firms that share no recorded joint venture with this one. Not a recorded relationship."
          >
            <ul className="flex flex-wrap gap-1.5">
              {predictedForFirm.slice(0, 6).map((p) => {
                const otherKey = p.keys[0] === entity.key ? p.keys[1] : p.keys[0];
                const otherName = p.keys[0] === entity.key ? p.firms[1] : p.firms[0];
                return (
                  <li key={otherKey}>
                    <button onClick={() => onSelectRelated(otherKey)} className="chip hover:border-accent" title={`similarity ${p.score}`}>
                      {otherName} <span className="tabular text-text-muted">· {p.score.toFixed(2)}</span>
                    </button>
                  </li>
                );
              })}
            </ul>
            <p className="mt-2 flex items-start gap-1.5 text-[11px] leading-relaxed text-text-muted">
              <Info size={13} className="mt-0.5 shrink-0" />
              A predicted tie is a statistical similarity only. It is not evidence of a relationship,
              coordination, or wrongdoing, and it has not been verified against any registry or filing.
            </p>
          </Section>
        )}

        {/* Curated, source-linked official actions and cases */}
        {ov && (
          <Section title="On the record">
            {ov.owner && (
              <p className="mb-3 text-sm text-text-secondary">
                <span className="text-text-muted">Reported owner: </span>
                {ov.owner}
              </p>
            )}
            <ul className="space-y-3">
              {ov.actions.map((a, i) => {
                const meta = ACTION_META[a.type];
                const src = source(a.source);
                const t = TONE[meta?.tone ?? "note"];
                return (
                  <li key={i} className={`rounded-lg border p-3 ${t.border}`}>
                    <div className="mb-1 flex items-center gap-2">
                      <span className={`chip ${t.chip}`}>{meta?.label ?? a.type}</span>
                      <span className="text-[11px] text-text-muted">{shortDate(a.date)}</span>
                    </div>
                    <p className="text-sm leading-relaxed text-text-secondary">{a.label}</p>
                    {src && (
                      <a href={src.url} target="_blank" rel="noopener noreferrer" className="link-source mt-1.5 inline-flex items-center gap-1 text-xs">
                        {src.label} <ArrowSquareOut size={12} />
                      </a>
                    )}
                  </li>
                );
              })}
            </ul>
            {ov.actions.some((a) => ACTION_META[a.type]?.tone === "alleged") && (
              <p className="mt-3 flex items-start gap-1.5 text-[11px] leading-relaxed text-text-muted">
                <Info size={13} className="mt-0.5 shrink-0" />
                Charges and audit flags are allegations under the presumption of innocence. Cases are pending unless a court has ruled otherwise.
              </p>
            )}
          </Section>
        )}

        {/* People tied to the firm (curated, sourced) */}
        {persons.length > 0 && (
          <Section title="People on record">
            <ul className="space-y-2.5">
              {persons.map((p) => (
                <li key={p.id} className="text-sm">
                  <p className="font-medium text-text-primary">{p.name}</p>
                  <p className="text-text-secondary">{p.role}</p>
                  <p className="mt-0.5 text-text-muted">{p.status}</p>
                  <div className="mt-1 flex flex-wrap gap-2">
                    {p.sources.map((sk) => {
                      const s = source(sk);
                      return s ? (
                        <a key={sk} href={s.url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1 text-xs">
                          Source <ArrowSquareOut size={11} />
                        </a>
                      ) : null;
                    })}
                  </div>
                </li>
              ))}
            </ul>
          </Section>
        )}

        {/* In the news */}
        {news && (
          <Section title="In the news">
            <a href={news.url} target="_blank" rel="noopener noreferrer" className="block rounded-lg border border-hairline p-3 hover:border-accent">
              <p className="text-sm leading-snug text-text-primary">{news.headline}</p>
              <p className="mt-1 text-xs text-text-muted">
                {news.source} · {shortDate(news.date)} · {news.articles}+ articles
              </p>
            </a>
            <p className="mt-2 text-[11px] leading-relaxed text-text-muted">
              Appearance in coverage is not a finding of wrongdoing. The link points to the source.
            </p>
          </Section>
        )}
      </div>
    </aside>
  );
}

function Section({ title, hint, children }: { title: string; hint?: string; children: React.ReactNode }) {
  return (
    <section className="mb-5 last:mb-0">
      <h3 className="mb-2 font-display text-[13px] font-semibold uppercase tracking-wide text-text-secondary">{title}</h3>
      {hint && <p className="mb-2 text-[11px] leading-relaxed text-text-muted">{hint}</p>}
      {children}
    </section>
  );
}

function Metric({ label, value, sub, tone, title }: { label: string; value: string; sub?: string; tone?: "signal"; title?: string }) {
  return (
    <div>
      <dt className="text-[11px] uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="tabular text-[15px] font-semibold" style={tone ? { color: "var(--signal)" } : { color: "var(--text-primary)" }} title={title}>
        {value}
      </dd>
      {sub && <dd className="text-[11px] text-text-muted">{sub}</dd>}
    </div>
  );
}
