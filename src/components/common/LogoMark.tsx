// A small knowledge-graph mark: four nodes joined into a web, echoing the
// site's own graph. Uses currentColor so it takes the accent from its parent.
export default function LogoMark({ size = 20, className = "" }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" className={className} aria-hidden="true">
      <g stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" opacity="0.5">
        <line x1="5.5" y1="7" x2="18" y2="5.5" />
        <line x1="5.5" y1="7" x2="15.5" y2="17.5" />
        <line x1="5.5" y1="7" x2="8.5" y2="16.5" />
        <line x1="18" y1="5.5" x2="15.5" y2="17.5" />
        <line x1="8.5" y1="16.5" x2="15.5" y2="17.5" />
      </g>
      <g fill="currentColor">
        <circle cx="5.5" cy="7" r="2" />
        <circle cx="18" cy="5.5" r="2" />
        <circle cx="15.5" cy="17.5" r="2.6" />
        <circle cx="8.5" cy="16.5" r="2" />
      </g>
    </svg>
  );
}
