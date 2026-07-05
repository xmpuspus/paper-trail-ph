"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { ArrowRight, CircleNotch } from "@phosphor-icons/react";
import type { GraphData, Overlay, InNews, Stats } from "@/lib/types";
import { peso } from "@/lib/format";

const GraphView = dynamic(() => import("@/components/graph/GraphView"), {
  ssr: false,
  loading: () => (
    <div className="flex h-full w-full items-center justify-center">
      <CircleNotch size={24} className="animate-spin text-text-muted" />
    </div>
  ),
});

interface Beat {
  eyebrow: string;
  title: string;
  body: React.ReactNode;
  stat?: { value: string; label: string };
  focus?: string | null; // firm key to highlight
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
  const refs = useRef<(HTMLDivElement | null)[]>([]);

  // Only mount the WebGL graph on desktop: initializing Sigma inside a
  // display:none container (mobile) throws and takes down the page.
  useEffect(() => {
    const mq = window.matchMedia("(min-width: 1024px)");
    const apply = () => setIsDesktop(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const beats: Beat[] = [
    {
      eyebrow: "The scale",
      title: "PHP 1.586 trillion, one category",
      body: (
        <>Between 2016 and 2026, DPWH recorded {stats.flood_control.contracts.toLocaleString()} flood-control
        and drainage contracts worth {peso(stats.flood_control.value)}. That is the second-largest infrastructure
        category by value in the whole dataset. This map starts there.</>
      ),
      stat: { value: peso(stats.flood_control.value), label: `across ${stats.flood_control.contracts.toLocaleString()} flood-control contracts` },
      focus: null,
    },
    {
      eyebrow: "Concentration",
      title: "The money pools in a few hands",
      body: (
        <>In {stats.concentration.concentrated_fc_deos} district offices, one or two firms hold most of the
        flood-control budget (a Herfindahl-Hirschman Index above 2,500, the US Department of Justice threshold for a
        highly concentrated market). News reporting and the administration&apos;s own review found about 15 firms
        received roughly PHP 100 billion, near 20% of the program. Who won the most is a question the records can answer.</>
      ),
      stat: { value: `${stats.concentration.concentrated_fc_deos}`, label: "district offices flagged as highly concentrated" },
      focus: null,
    },
    {
      eyebrow: "One family, nine firms",
      title: "The Discaya companies",
      body: (
        <>On September 1, 2025, Sarah Discaya told a Senate hearing she owned nine construction firms. Two days
        later, the Philippine Contractors Accreditation Board revoked all nine licenses (Board Resolution 075) for
        collusion and bid-rigging. Several appear here as top flood-control awardees, and the DPWH dataset already
        marks their licenses as revoked. Select St. Gerrard to see its network.</>
      ),
      stat: { value: "9", label: "firms, licenses revoked by PCAB (Sept 2025)" },
      focus: "31762",
    },
    {
      eyebrow: "The first charges",
      title: "Sunwest and Zaldy Co",
      body: (
        <>In November 2025 the Ombudsman filed the first criminal charges of the scandal before the Sandiganbayan:
        graft and malversation against company directors and resigned representative Zaldy Co, over a
        PHP 289.5-million flood-control project in Oriental Mindoro. Charges are allegations; the case is pending.</>
      ),
      stat: { value: peso(stats.top_flood_control_firms.find((f) => f.key === "15906")?.fc_value ?? 0), label: "Sunwest recorded flood-control value" },
      focus: "15906",
    },
    {
      eyebrow: "Flags and blacklists",
      title: "Topnotch, Wawao, and the audits",
      body: (
        <>The Commission on Audit flagged a Topnotch Catalyst Builders riverbank project in Bulacan in a fraud audit
        report. DPWH ordered the perpetual disqualification of Wawao Builders and SYMS Construction for ghost
        projects. Each of these is a recorded official action or an audit flag, linked to its source on the firm&apos;s card.</>
      ),
      stat: { value: `${stats.revoked.firms}`, label: "firms with DPWH licenses recorded as revoked" },
      focus: "34061",
    },
    {
      eyebrow: "What this is",
      title: "Indicators, not verdicts",
      body: (
        <>Everything here is a public record: a contract, a license status, a court filing, an audit report. The graph
        computes statistical indicators, concentration, who co-awards with whom, who won the most. It does not decide
        guilt. Charges are allegations under the presumption of innocence. Every claim links to its source.</>
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
    <section id="story" className="scroll-mt-20">
      <div className="mb-6">
        <p className="eyebrow">The flood-control scandal, beat by beat</p>
        <h2 className="mt-1 font-display text-2xl font-bold text-text-primary md:text-3xl">Walk the paper trail</h2>
      </div>

      <div className="grid gap-8 lg:grid-cols-[420px_1fr]">
        {/* Scrolling narrative */}
        <div className="order-2 lg:order-1">
          {beats.map((b, i) => (
            <div
              key={i}
              ref={(el) => { refs.current[i] = el; }}
              className={`mb-6 rounded-xl border p-5 transition-colors last:mb-0 ${active === i ? "border-accent bg-surface" : "border-hairline bg-surface/40"}`}
            >
              <p className="eyebrow">{b.eyebrow}</p>
              <h3 className="mt-1.5 font-display text-xl font-bold text-text-primary">{b.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-text-secondary">{b.body}</p>
              {b.stat && (
                <div className="mt-3 border-t border-hairline pt-3">
                  <span className="tabular font-display text-2xl font-bold text-signal">{b.stat.value}</span>
                  <span className="ml-2 text-xs text-text-muted">{b.stat.label}</span>
                </div>
              )}
              {b.focus && (
                <a href="#explore" className="link-source mt-3 inline-flex items-center gap-1 text-xs">
                  Open this firm in the explorer <ArrowRight size={12} />
                </a>
              )}
            </div>
          ))}
        </div>

        {/* Sticky graph that reacts to the active beat (desktop only) */}
        {isDesktop && (
          <div className="order-1 lg:order-2 lg:sticky lg:top-20 lg:h-[calc(100vh-6rem)]">
            <div className="h-[70vh] overflow-hidden rounded-xl border border-hairline bg-page">
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
            <p className="mt-2 text-center text-xs text-text-muted">
              Scandal core: the highest-value flood-control firms, their district offices, and recorded joint ventures. Node size = recorded value.
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
