"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Graph from "graphology";
import forceAtlas2 from "graphology-layout-forceatlas2";
import { Play, Pause, ArrowCounterClockwise } from "@phosphor-icons/react";
import type { GraphData, Overlay, InNews } from "@/lib/types";
import { nodeStatus, nodeRadius, cssColor } from "@/lib/tiers";

interface Props {
  data: GraphData;
  overlay: Overlay | null;
  inNews: InNews | null;
}

interface LNode {
  id: string;
  x: number; // normalized 0..1
  y: number;
  r: number; // base radius (px at 1x)
  status: string; // colour resolved live per theme in the draw loop
  square: boolean;
  reveal: number; // year this node first connects in this subgraph
  label: string | null;
}

// Colours resolved from the LIVE data-theme attribute (ThemeProvider sets it in
// an effect that runs AFTER child effects, so reading it at setup time gets the
// stale theme; the draw loop re-reads only when data-theme actually changes).
function palette() {
  return {
    edge: cssColor("--tier-recorded", "#59616b"),
    jv: cssColor("--signal", "#a5610a"),
    bg: cssColor("--graph-bg", "#fafbfc"),
    label: cssColor("--graph-label", "#4b5158"),
    status: {
      alleged: cssColor("--alert", "#b3341d"),
      action: cssColor("--signal", "#a5610a"),
      news: cssColor("--water", "#0f7d8c"),
      entity: cssColor("--node-entity", "#1a56db"),
      person: cssColor("--node-person", "#6d4ea3"),
      normal: cssColor("--node-contractor", "#9aa2ab"),
    } as Record<string, string>,
  };
}
interface LEdge {
  ax: number; ay: number; bx: number; by: number;
  reveal: number;
  jv: boolean; // joint venture (vs award)
  w: number; // number of flood-control contracts on this link
}

// Link width scales with the number of contracts (sqrt so a 50-contract link
// is thicker but not 50x a 1-contract link).
const edgeWidth = (w: number, jv: boolean) =>
  clamp((jv ? 0.8 : 0.45) + 0.5 * Math.sqrt(w), 0.5, 5);

const DUR_MS = 15000; // full replay length
const ease = (t: number) => 1 - (1 - t) * (1 - t); // easeOutQuad

export default function GraphTimeline({ data, overlay, inNews }: Props) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [reduced, setReduced] = useState(false);
  const [playing, setPlaying] = useState(false);
  const [year, setYear] = useState(0); // integer, current
  const [ended, setEnded] = useState(false);

  // Refs the animation loop reads without restarting.
  const tRef = useRef(0);
  const playingRef = useRef(false);
  const startedRef = useRef(false);
  const interactedRef = useRef(false); // any manual control disables auto-play

  // Only the recorded contract structure forms the replay.
  const { nodes, edges, minYear, maxYear, statsByYear, spanX, spanY } = useMemo(() => {
    const keepNode = (t: string) => t === "Contractor" || t === "ProcuringEntity";
    const keepEdge = (t: string) => t === "AWARDED_TO" || t === "CO_AWARDED_WITH";
    const rnodes = data.nodes.filter((n) => keepNode(n.type));
    const redges = data.edges.filter((e) => keepEdge(e.type));

    const years = redges.map((e) => e.first_year).filter((y): y is number => y != null);
    const minY = years.length ? Math.min(...years) : 2016;
    const maxY = years.length ? Math.max(...years) : 2025;

    // Frozen layout: compute once with ForceAtlas2, then reveal by year.
    // Seed on a circle (deterministic, symmetric) so the result is reproducible
    // and converges to a rounded, cohesive shape rather than a random smear. Node
    // sizes feed adjustSizes so big nodes don't overlap.
    const g = new Graph({ multi: false });
    const N = rnodes.length || 1;
    rnodes.forEach((n, i) => {
      if (!g.hasNode(n.id)) {
        const ang = (2 * Math.PI * i) / N;
        g.addNode(n.id, { x: Math.cos(ang) * 100, y: Math.sin(ang) * 100, size: Math.max(2.5, nodeRadius(n)) });
      }
    });
    redges.forEach((e) => {
      if (g.hasNode(e.source) && g.hasNode(e.target) && !g.hasEdge(e.source, e.target)) {
        g.addEdgeWithKey(e.id, e.source, e.target, { weight: e.weight || 1 });
      }
    });
    const big = g.order > 900;
    // linLog + outbound attraction pulls firms toward the offices they win in,
    // gravity keeps the whole thing cohesive, adjustSizes spaces the marks.
    forceAtlas2.assign(g, {
      iterations: big ? 150 : 600,
      settings: {
        linLogMode: true,
        outboundAttractionDistribution: true,
        adjustSizes: true,
        barnesHutOptimize: true,
        gravity: 1.1,
        scalingRatio: 9,
        slowDown: 9,
      },
    });

    // Node reveal = the first year an incident edge appears (no floating nodes).
    const reveal = new Map<string, number>();
    redges.forEach((e) => {
      const y = e.first_year ?? minY;
      for (const nd of [e.source, e.target]) {
        const cur = reveal.get(nd);
        if (cur == null || y < cur) reveal.set(nd, y);
      }
    });

    let minX = Infinity, maxX = -Infinity, minPy = Infinity, maxPy = -Infinity;
    g.forEachNode((id, a) => {
      minX = Math.min(minX, a.x); maxX = Math.max(maxX, a.x);
      minPy = Math.min(minPy, a.y); maxPy = Math.max(maxPy, a.y);
    });
    const spanX = maxX - minX || 1, spanY = maxPy - minPy || 1;
    const midX = (minX + maxX) / 2, midY = (minPy + maxPy) / 2;

    // Label the largest few named firms once they appear.
    const labelled = new Set(
      [...rnodes].filter((n) => n.type === "Contractor").sort((a, b) => (b.fc_value ?? 0) - (a.fc_value ?? 0)).slice(0, 6).map((n) => n.id),
    );

    // Centre the layout in its own units; the draw loop fits it with a single
    // uniform scale so the true (roughly round) proportions are preserved.
    const posOf = (id: string) => {
      const a = g.getNodeAttributes(id);
      return { x: a.x - midX, y: a.y - midY };
    };

    const lnodes: LNode[] = rnodes.map((n) => {
      const p = posOf(n.id);
      return {
        id: n.id, x: p.x, y: p.y,
        r: Math.max(2.5, nodeRadius(n) * 1.15),
        status: nodeStatus(n, overlay, inNews),
        square: n.type === "ProcuringEntity",
        reveal: reveal.get(n.id) ?? minY,
        label: labelled.has(n.id) ? n.label : null,
      };
    });
    const ledges: LEdge[] = redges
      .filter((e) => g.hasNode(e.source) && g.hasNode(e.target))
      .map((e) => {
        const a = posOf(e.source), b = posOf(e.target);
        return { ax: a.x, ay: a.y, bx: b.x, by: b.y, reveal: e.first_year ?? minY, jv: e.type === "CO_AWARDED_WITH", w: e.weight || 1 };
      });

    // Cumulative counters + largest connected group per integer year.
    const idIndex = new Map(rnodes.map((n, i) => [n.id, i]));
    const statsByYear = new Map<number, { nodes: number; edges: number; giant: number }>();
    for (let y = minY; y <= maxY; y++) {
      const parent = rnodes.map((_, i) => i);
      const find = (i: number): number => (parent[i] === i ? i : (parent[i] = find(parent[i])));
      let ecount = 0;
      redges.forEach((e) => {
        if ((e.first_year ?? minY) <= y) {
          ecount++;
          const a = idIndex.get(e.source), b = idIndex.get(e.target);
          if (a != null && b != null) parent[find(a)] = find(b);
        }
      });
      const shown = new Set<number>();
      const size = new Map<number, number>();
      rnodes.forEach((n, i) => {
        if ((reveal.get(n.id) ?? minY) <= y) {
          shown.add(i);
          const root = find(i);
          size.set(root, (size.get(root) ?? 0) + 1);
        }
      });
      let giant = 0;
      shown.forEach((i) => { const s = size.get(find(i)) ?? 1; if (s > giant) giant = s; });
      statsByYear.set(y, { nodes: shown.size, edges: ecount, giant });
    }

    // Layout + status keys only; colours are theme-resolved in the draw loop, so
    // this does not depend on theme and never re-lays-out on a theme toggle.
    return { nodes: lnodes, edges: ledges, minYear: minY, maxYear: maxY, statsByYear, spanX, spanY };
  }, [data, overlay, inNews]);

  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)");
    const apply = () => setReduced(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  useEffect(() => { tRef.current = minYear; setYear(minYear); }, [minYear]);
  useEffect(() => { playingRef.current = playing; }, [playing]);

  const play = useCallback(() => {
    if (tRef.current >= maxYear + 0.99) { tRef.current = minYear; setYear(minYear); }
    setEnded(false);
    playingRef.current = true; // take effect this frame, not next render
    setPlaying(true);
  }, [minYear, maxYear]);

  const pause = useCallback(() => {
    playingRef.current = false;
    setPlaying(false);
  }, []);

  // Draw + advance loop.
  useEffect(() => {
    const canvas = canvasRef.current;
    const wrap = wrapRef.current;
    if (!canvas || !wrap) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let C = palette();
    let paletteTheme = document.documentElement.getAttribute("data-theme");
    const dpr = Math.min(2, window.devicePixelRatio || 1);
    let W = 0, H = 0, scale = 1;
    const PAD = 34;

    const resize = () => {
      const cw = wrap.clientWidth;
      // Taller, less extreme aspect gives the round layout room to breathe.
      const ch = Math.max(360, Math.min(600, Math.round(cw * 0.66)));
      W = cw; H = ch;
      // One uniform scale for both axes: preserves the layout's true proportions
      // (no horizontal stretch), fit to whichever dimension is tighter, centred.
      scale = Math.min((W - 2 * PAD) / spanX, (H - 2 * PAD) / spanY);
      canvas.width = cw * dpr; canvas.height = ch * dpr;
      canvas.style.width = cw + "px"; canvas.style.height = ch + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(wrap);

    const X = (nx: number) => W / 2 + nx * scale;
    const Y = (ny: number) => H / 2 + ny * scale;

    let raf = 0;
    let last = 0;
    const frame = (ts: number) => {
      const dt = last ? ts - last : 16;
      last = ts;
      const th = document.documentElement.getAttribute("data-theme");
      if (th !== paletteTheme) { paletteTheme = th; C = palette(); }
      if (playingRef.current && !reduced) {
        const span = maxYear + 1 - minYear;
        tRef.current += (dt / DUR_MS) * span;
        if (tRef.current >= maxYear + 1) {
          tRef.current = maxYear + 1;
          playingRef.current = false;
          setPlaying(false);
          setEnded(true);
        }
        const yi = Math.min(maxYear, Math.floor(tRef.current));
        setYear((prev) => (prev !== yi ? yi : prev));
      }
      const t = tRef.current;
      const curYear = Math.min(maxYear, Math.floor(t));

      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = C.bg;
      ctx.fillRect(0, 0, W, H);

      // edges
      ctx.lineCap = "round";
      for (const e of edges) {
        if (e.reveal > curYear) continue;
        const frac = e.reveal === curYear ? clamp(t - e.reveal, 0, 1) : 1;
        ctx.globalAlpha = (e.jv ? 0.7 : 0.3) * frac;
        ctx.strokeStyle = e.jv ? C.jv : C.edge;
        ctx.lineWidth = edgeWidth(e.w, e.jv);
        ctx.beginPath();
        ctx.moveTo(X(e.ax), Y(e.ay));
        ctx.lineTo(X(e.bx), Y(e.by));
        ctx.stroke();
      }
      // nodes
      ctx.globalAlpha = 1;
      for (const n of nodes) {
        if (n.reveal > curYear) continue;
        const pop = n.reveal === curYear ? ease(clamp(t - n.reveal, 0, 1)) : 1;
        const r = n.r * (0.3 + 0.7 * pop);
        const px = X(n.x), py = Y(n.y);
        ctx.fillStyle = C.status[n.status] ?? C.status.normal;
        ctx.globalAlpha = 0.4 + 0.6 * pop;
        // A thin surface-coloured ring separates overlapping marks.
        ctx.strokeStyle = C.bg;
        ctx.lineWidth = 1.2;
        if (n.square) {
          ctx.fillRect(px - r, py - r, r * 2, r * 2);
          ctx.strokeRect(px - r, py - r, r * 2, r * 2);
        } else {
          ctx.beginPath();
          ctx.arc(px, py, r, 0, Math.PI * 2);
          ctx.fill();
          ctx.stroke();
        }
      }
      // labels (named firms, once solidly in)
      ctx.globalAlpha = 1;
      ctx.font = "600 11px var(--font-body), system-ui, sans-serif";
      ctx.fillStyle = C.label;
      ctx.textBaseline = "middle";
      for (const n of nodes) {
        if (!n.label || n.reveal > curYear) continue;
        const a = clamp(t - n.reveal, 0, 1);
        ctx.globalAlpha = 0.85 * a;
        ctx.fillText(n.label, X(n.x) + n.r + 3, Y(n.y));
      }
      ctx.globalAlpha = 1;
      raf = requestAnimationFrame(frame);
    };
    raf = requestAnimationFrame(frame);
    return () => { cancelAnimationFrame(raf); ro.disconnect(); };
  }, [nodes, edges, minYear, maxYear, reduced, spanX, spanY]);

  // Auto-play once when scrolled into view (unless reduced motion).
  useEffect(() => {
    const wrap = wrapRef.current;
    if (!wrap || reduced) return;
    const io = new IntersectionObserver(
      (ents) => {
        ents.forEach((e) => {
          if (e.isIntersecting && !startedRef.current && !interactedRef.current) {
            startedRef.current = true;
            play();
          }
        });
      },
      { threshold: 0.4 },
    );
    io.observe(wrap);
    return () => io.disconnect();
  }, [reduced, play]);

  const s = statsByYear.get(year) ?? { nodes: 0, edges: 0, giant: 0 };

  return (
    <figure className="rounded-xl border border-hairline p-3" style={{ background: "var(--graph-bg)" }}>
      <div className="mb-2 flex flex-wrap items-center gap-x-4 gap-y-2 px-1">
        <div className="flex items-center gap-2">
          {ended ? (
            <button onClick={() => { interactedRef.current = true; play(); }} className="btn btn-primary text-[13px]" aria-label="Replay">
              <ArrowCounterClockwise size={15} /> Replay
            </button>
          ) : (
            <button
              onClick={() => { interactedRef.current = true; playing ? pause() : play(); }}
              className="btn btn-primary text-[13px]"
              aria-label={playing ? "Pause" : "Play"}
              disabled={reduced}
            >
              {playing ? <Pause size={15} weight="fill" /> : <Play size={15} weight="fill" />}
              {playing ? "Pause" : "Play"}
            </button>
          )}
          <span className="figure text-[22px] tabular text-text-primary" aria-live="polite">{year}</span>
        </div>
        <input
          type="range"
          min={minYear}
          max={maxYear}
          value={year}
          onChange={(e) => {
            const y = Number(e.target.value);
            interactedRef.current = true;
            playingRef.current = false;
            setPlaying(false);
            setEnded(y >= maxYear);
            tRef.current = y === maxYear ? maxYear + 0.999 : y;
            setYear(y);
          }}
          aria-label="Year"
          className="h-1 min-w-[140px] flex-1 cursor-pointer accent-accent"
        />
        <div className="tabular flex flex-wrap gap-x-4 gap-y-0.5 text-[13px] text-text-secondary">
          <span><span className="text-text-primary">{s.nodes}</span> firms &amp; offices</span>
          <span><span className="text-text-primary">{s.edges}</span> links</span>
          <span>largest group <span className="text-text-primary">{s.giant}</span></span>
        </div>
      </div>
      <div ref={wrapRef} className="w-full overflow-hidden rounded-lg">
        <canvas ref={canvasRef} role="img" aria-label={`Flood-control network in ${year}: ${s.nodes} firms and offices, ${s.edges} recorded links, largest connected group ${s.giant}`} />
      </div>
      <figcaption className="mt-2 px-1 text-[11px] leading-relaxed text-text-muted">
        Replay of the scandal-core network forming, {minYear} to {maxYear}: firms (circles) and district offices (squares)
        appear when they first connect, award links in grey, recorded joint ventures in ochre. Link width scales with the
        number of flood-control contracts; node size with recorded contract value; positions are fixed so the growth reads
        as densification. Node colour marks the record on a firm. Descriptive, from public data.
      </figcaption>
    </figure>
  );
}

function clamp(v: number, lo: number, hi: number) {
  return v < lo ? lo : v > hi ? hi : v;
}
