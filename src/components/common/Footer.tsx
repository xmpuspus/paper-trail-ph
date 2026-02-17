import { DISCLAIMER } from "@/lib/constants";

export default function Footer() {
  return (
    <footer
      className="px-4 py-3 text-xs"
      style={{
        borderTop: "1px solid var(--color-border)",
        backgroundColor: "var(--color-surface)",
        color: "var(--color-text-muted)",
      }}
    >
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="flex-1 min-w-[200px]">{DISCLAIMER}</p>
        <div className="flex flex-wrap gap-4">
          <a
            href="https://github.com/xmpuspus/paper-trail-ph"
            target="_blank"
            rel="noopener noreferrer"
            className="transition-colors"
            style={{ color: "var(--color-text-muted)" }}
          >
            GitHub
          </a>
          <a
            href="/data-sources"
            className="transition-colors"
            style={{ color: "var(--color-text-muted)" }}
          >
            Data Sources
          </a>
          <a
            href="/methodology"
            className="transition-colors"
            style={{ color: "var(--color-text-muted)" }}
          >
            Methodology
          </a>
        </div>
      </div>
    </footer>
  );
}
