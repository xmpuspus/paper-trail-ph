"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { ArrowRight, ArrowSquareOut, CircleNotch } from "@phosphor-icons/react";
import type { GraphData, Overlay, InNews, Stats } from "@/lib/types";
import { peso } from "@/lib/format";

const GraphView = dynamic(() => import("@/components/graph/GraphView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      <CircleNotch size={22} className="animate-spin text-text-muted" />
    </div>
  ),
});

interface Beat {
  eyebrow: string;
  title: string;
  body: React.ReactNode;
  figure?: { value: string; label: string; tone?: boolean };
  source?: { label: string; url: string };
  focus?: string | null;
}

interface Props {
  scandalGraph: GraphData;
  overlay: Overlay;
  inNews: InNews;
  stats: Stats;
}

export default function StoryRail({ scandalGraph, overlay, inNews, stats }: Props) {
  const [active, setActive] = useState(0);
  const [isDesktop, setIsDesktop] = useState(false);
  const refs = useRef<(HTMLLIElement | null)[]>([]);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const apply = () => setIsDesktop(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const sunwestFc = stats.top_flood_control_firms.find((f) => f.key === "15906")?.fc_value ?? 0;

  const beats: Beat[] = [
    {
      eyebrow: "The scale",
      title: "One category, ₱1.586 trillion",
      body: (
        <>Between 2016 and 2026, DPWH recorded {stats.flood_control.contracts.toLocaleString()} flood-control
        and drainage contracts. By value it is the second-largest infrastructure category in the whole dataset,
        behind only roads.</>
      ),
      figure: { value: peso(stats.flood_control.value), label: "recorded flood-control value", tone: true },
      focus: null,
    },
    {
      eyebrow: "The surge",
      title: "Spending tripled in six years",
      body: (
        <>Flood-control allocations climbed from about ₱124 billion in infrastructure year 2018 to ₱368 billion in
        2024, the peak year, before easing in 2025. Most of the contested projects sit inside that run-up.</>
      ),
      figure: { value: "₱368B", label: "flood-control value, 2024 (the peak)" },
      focus: null,
    },
    {
      eyebrow: "Concentration",
      title: "Twenty district offices with high concentration",
      body: (
        <>In {stats.concentration.concentrated_fc_deos} district engineering offices, one or two firms hold most of
        the flood-control budget: a Herfindahl-Hirschman Index above 2,500, the US Justice Department line for a
        highly concentrated market. News reporting and the administration&apos;s own review found about 15 firms took
        roughly ₱100 billion, near 20% of the program.</>
      ),
      figure: { value: `${stats.concentration.concentrated_fc_deos}`, label: "highly concentrated district offices" },
      source: { label: "Flood control scandal (Wikipedia)", url: "https://en.wikipedia.org/wiki/Flood_control_projects_scandal_in_the_Philippines" },
      focus: null,
    },
    {
      eyebrow: "The epicenter",
      title: "Bulacan, where COA flagged unbuilt projects",
      body: (
        <>Flood-control contracts in Bulacan&apos;s district offices total about ₱102.9 billion. This is where the
        Commission on Audit found projects paid for but unbuilt, and where the top awardees include Wawao Builders
        and Topnotch Catalyst Builders.</>
      ),
      figure: { value: "₱102.9B", label: "flood-control value in Bulacan offices" },
      source: { label: "COA fraud audits (Rappler)", url: "https://www.rappler.com/philippines/luzon/coa-flags-ghost-bulacan-flood-projects-fraud-audit-october-2-2025/" },
      focus: "46535",
    },
    {
      eyebrow: "The reach",
      title: "A few firms across dozens of offices",
      body: (
        <>A handful of contractors do not just win in one place. St. Gerrard Construction appears as a flood-control
        awardee across 96 district offices; St. Timothy across 82; Legacy across 87. In the graph they sit between
        clusters, with the widest reach across offices.</>
      ),
      figure: { value: "96", label: "district offices touched by one firm" },
      focus: "31762",
    },
    {
      eyebrow: "One family, nine firms",
      title: "The Discaya companies",
      body: (
        <>On September 1, 2025, Sarah Discaya told a Senate hearing she owned nine construction firms. Two days later
        the Philippine Contractors Accreditation Board revoked all nine licenses (Board Resolution 075) for collusion
        and bid-rigging. Several appear here as top flood-control awardees, and the DPWH dataset already marks their
        licenses as revoked.</>
      ),
      figure: { value: "9", label: "firms, licenses revoked by PCAB" },
      source: { label: "9 Discaya firms stripped of license (Inquirer)", url: "https://newsinfo.inquirer.net/2104392/9-discaya-firms-stripped-of-license-as-contractors" },
      focus: "38958",
    },
    {
      eyebrow: "The first charges",
      title: "Sunwest and Zaldy Co",
      body: (
        <>In November 2025 the Ombudsman filed the first criminal charges in the flood-control case before the Sandiganbayan:
        graft and malversation against company directors and resigned representative Zaldy Co, over a
        ₱289.5-million flood-control project in Oriental Mindoro. Charges are allegations; the case is pending.</>
      ),
      figure: { value: peso(sunwestFc), label: "Sunwest recorded flood-control value" },
      source: { label: "Sandiganbayan cases vs Zaldy Co (GMA)", url: "https://www.gmanetwork.com/news/topstories/nation/966658/sandiganbayan-raffles-off-cases-vs-zaldy-co-others-over-flood-control-mess/" },
      focus: "15906",
    },
    {
      eyebrow: "Flags and freezes",
      title: "Audits, blacklists, frozen assets",
      body: (
        <>The Commission on Audit flagged a Topnotch riverbank project in Bulacan. Separately, the anti-money-laundering
        council secured court orders freezing assets tied to the Discaya family. DPWH ordered the perpetual
        disqualification of Wawao Builders and SYMS. Even so, the eight firms carrying a revoked-license tag in the data
        won about ₱74.5 billion in flood control alone.</>
      ),
      figure: { value: "₱74.5B", label: "flood-control won by revoked-license firms" },
      source: { label: "DPWH bans Wawao, SYMS (Manila Times)", url: "https://www.manilatimes.net/2025/09/05/news/national/dpwh-secretary-dizon-orders-perpetual-ban-of-wawao-builders-syms-construction-for-ghost-projects/2179262" },
      focus: "34061",
    },
    {
      eyebrow: "What this is",
      title: "Not verdicts, but indicators",
      body: (
        <>Everything here is a public record: a contract, a license status, a court filing, an audit report. The graph
        computes statistical indicators, who co-awards with whom, who won the most, where the money concentrates. It
        does not decide guilt. Charges are allegations under the presumption of innocence, and every claim links to its
        source.</>
      ),
      focus: null,
    },
  ];

  useEffect(() => {
    const obs = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const i = refs.current.findIndex((r) => r === e.target);
            if (i >= 0) setActive(i);
          }
        });
      },
      { rootMargin: "-45% 0px -45% 0px", threshold: 0 },
    );
    refs.current.forEach((r) => r && obs.observe(r));
    return () => obs.disconnect();
  }, []);

  const focusKey = beats[active]?.focus ?? null;

  return (
    <section id="story" className="scroll-mt-24">
      <p className="eyebrow-muted">Reading the record, in sequence</p>
      <h2 className="mt-2 max-w-2xl text-[28px] font-bold tracking-tight text-text-primary md:text-[38px]">
        What the records show
      </h2>

      <div className="mt-10 grid gap-10 lg:grid-cols-[minmax(0,440px)_1fr]">
        {/* Narrative */}
        <ol className="order-2 lg:order-1">
          {beats.map((b, i) => (
            <li
              key={i}
              ref={(el) => { refs.current[i] = el; }}
              className={`border-t border-hairline py-8 transition-opacity first:border-t-0 first:pt-0 ${active === i ? "opacity-100" : "lg:opacity-45"}`}
            >
              <div className="flex items-baseline gap-3">
                <span className="tabular text-sm text-text-muted">{String(i + 1).padStart(2, "0")}</span>
                <span className="eyebrow">{b.eyebrow}</span>
              </div>
              <h3 className="mt-2 text-[22px] font-semibold tracking-tight text-text-primary">{b.title}</h3>
              <p className="mt-2.5 text-[15px] leading-relaxed text-text-secondary">{b.body}</p>
              {b.figure && (
                <p className="mt-4">
                  <span className="figure text-[26px]" style={b.figure.tone ? { color: "var(--signal)" } : { color: "var(--text-primary)" }}>{b.figure.value}</span>
                  <span className="ml-2.5 text-[13px] text-text-muted">{b.figure.label}</span>
                </p>
              )}
              <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-1.5">
                {b.source && (
                  <a href={b.source.url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1 text-[13px]">
                    {b.source.label} <ArrowSquareOut size={11} />
                  </a>
                )}
                {b.focus && (
                  <a href="#explore" className="inline-flex items-center gap-1 text-[13px] text-accent">
                    Open in the explorer <ArrowRight size={12} />
                  </a>
                )}
              </div>
            </li>
          ))}
        </ol>

        {/* Sticky graph, desktop only */}
        {isDesktop && (
          <div className="order-1 lg:order-2 lg:sticky lg:top-24 lg:h-[calc(100vh-7rem)]">
            <div className="h-[72vh] overflow-hidden rounded-xl border border-hairline" style={{ background: "var(--graph-bg)" }}>
              <GraphView
                data={scandalGraph}
                colorBy="status"
                showDerived={false}
                overlay={overlay}
                inNews={inNews}
                selected={focusKey}
                onSelect={() => {}}
              />
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-text-muted">
              The named firms and the offices they share: the highest-value flood-control firms, their district offices (squares), and recorded
              joint ventures. Node size is the recorded contract value. Colour marks the record on a firm.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
