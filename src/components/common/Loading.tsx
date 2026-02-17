import { useState, useEffect } from "react";

export function Spinner({ className = "" }: { className?: string }) {
  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div
        className="h-6 w-6 animate-spin rounded-full border-2"
        style={{
          borderColor: "var(--color-border)",
          borderTopColor: "var(--color-text-muted)",
        }}
      />
    </div>
  );
}

export function SkeletonLoader({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg ${className}`}
      style={{ backgroundColor: "var(--skeleton-bg)" }}
    />
  );
}

export function PanelSkeleton() {
  return (
    <div className="space-y-4 p-4">
      <SkeletonLoader className="h-8 w-3/4" />
      <SkeletonLoader className="h-4 w-full" />
      <SkeletonLoader className="h-4 w-5/6" />
      <SkeletonLoader className="h-32 w-full" />
      <SkeletonLoader className="h-4 w-full" />
      <SkeletonLoader className="h-4 w-4/6" />
    </div>
  );
}

export function GraphLoadingState() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), 6_000);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div
      className="flex h-full w-full items-center justify-center"
      style={{ backgroundColor: "var(--color-bg)" }}
    >
      <div className="text-center">
        <div
          className="mb-3 inline-block h-8 w-8 animate-spin rounded-full border-2"
          style={{
            borderColor: "var(--color-border)",
            borderTopColor: "var(--color-text-muted)",
          }}
        />
        <p className="text-xs" style={{ color: "var(--color-text-muted)" }}>
          {slow ? "Waking up server — this can take up to a minute on free tier..." : "Loading graph..."}
        </p>
      </div>
    </div>
  );
}
