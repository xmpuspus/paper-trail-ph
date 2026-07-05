// Peso and number formatting. Figures are shown in a monospace ledger style.

export function peso(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return "—";
  if (amount >= 1e12) return `₱${(amount / 1e12).toFixed(3)}T`;
  if (amount >= 1e9) return `₱${(amount / 1e9).toFixed(2)}B`;
  if (amount >= 1e6) return `₱${(amount / 1e6).toFixed(1)}M`;
  if (amount >= 1e3) return `₱${(amount / 1e3).toFixed(0)}K`;
  return `₱${Math.round(amount)}`;
}

const PESO_FULL = new Intl.NumberFormat("en-PH", {
  style: "currency",
  currency: "PHP",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function pesoFull(amount: number | null | undefined): string {
  if (amount == null || isNaN(amount)) return "—";
  return PESO_FULL.format(amount);
}

export function num(n: number | null | undefined): string {
  if (n == null || isNaN(n)) return "—";
  return n.toLocaleString("en-US");
}

export function shortDate(iso: string): string {
  // Accepts "2025-09" or "2025-09-03"; renders "Sep 2025" / "Sep 3, 2025".
  const parts = iso.split("-");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  const y = parts[0];
  const m = parts[1] ? months[parseInt(parts[1], 10) - 1] : "";
  const d = parts[2] ? String(parseInt(parts[2], 10)) : "";
  if (d) return `${m} ${d}, ${y}`;
  if (m) return `${m} ${y}`;
  return y;
}
