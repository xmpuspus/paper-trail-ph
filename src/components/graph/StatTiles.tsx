interface Tile {
  label: string;
  value: string;
  sub?: string;
  tone?: "signal" | "alert" | "water" | "good";
}

const TONE_VAR: Record<string, string> = {
  signal: "var(--signal)",
  alert: "var(--alert)",
  water: "var(--water)",
  good: "var(--good)",
};

export default function StatTiles({ tiles }: { tiles: Tile[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
      {tiles.map((t) => (
        <div key={t.label} className="stat-tile">
          <p className="eyebrow mb-2">{t.label}</p>
          <p
            className="stat-value text-[30px] md:text-[34px]"
            style={t.tone ? { color: TONE_VAR[t.tone] } : { color: "var(--text-primary)" }}
          >
            {t.value}
          </p>
          {t.sub && <p className="mt-1.5 text-xs text-text-muted">{t.sub}</p>}
        </div>
      ))}
    </div>
  );
}
