import { ArrowSquareOut } from "@phosphor-icons/react/dist/ssr";

const RELATED = [
  { label: "BetterGov.PH flood visualizations", url: "https://visualizations.bettergov.ph/flood" },
  { label: "Rappler Politicontractors", url: "https://www.rappler.com/newsbreak/investigative/politicians-government-contractors-connections-map/" },
  { label: "InfraWatch PH", url: "https://infrawatchph.org/home/contractors" },
  { label: "PCIJ MoneyPolitics", url: "https://moneypolitics.pcij.org/" },
  { label: "OCCRP Aleph", url: "https://aleph.occrp.org/" },
  { label: "LittleSis", url: "https://littlesis.org/" },
];

export default function Footer() {
  return (
    <footer className="mt-20 border-t border-hairline bg-surface">
      <div className="mx-auto max-w-content px-4 py-10 md:px-6">
        <p className="max-w-3xl text-sm leading-relaxed text-text-secondary">
          All data sourced from public records (COA, SEC, DBM, PSA, BSP, SALN disclosures). This tool computes statistical
          indicators only. Specific allegations, if any, require independent investigation and corroboration.
        </p>

        <div className="mt-6">
          <p className="eyebrow mb-2">Related projects</p>
          <ul className="flex flex-wrap gap-x-5 gap-y-1.5 text-sm">
            {RELATED.map((r) => (
              <li key={r.url}>
                <a href={r.url} target="_blank" rel="noopener noreferrer" className="link-source inline-flex items-center gap-1">
                  {r.label} <ArrowSquareOut size={11} />
                </a>
              </li>
            ))}
          </ul>
        </div>

        <p className="mt-6 text-xs text-text-muted">
          Not affiliated with any government agency. Data is CC0 1.0 (public domain), maintained by BetterGov.PH.{" "}
          <a href="https://github.com/xmpuspus/paper-trail-ph" target="_blank" rel="noopener noreferrer" className="link-source">Source on GitHub</a>.
        </p>
      </div>
    </footer>
  );
}
