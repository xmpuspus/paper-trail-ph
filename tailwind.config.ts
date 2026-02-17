import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        /* Node type colors (static) */
        politician: "#0038A8",
        "political-family": "#1A1A5E",
        agency: "#0D7377",
        contract: "#D4A843",
        contractor: "#2E7D32",
        "audit-finding": "#D32F2F",
        municipality: "#607D8B",
        bill: "#7B1FA2",
        person: "#8D6E63",

        /* Theme-aware colors via CSS variables */
        "th-bg": "var(--color-bg)",
        "th-surface": "var(--color-surface)",
        "th-surface-elevated": "var(--color-surface-elevated)",
        "th-surface-hover": "var(--color-surface-hover)",
        "th-text": "var(--color-text-primary)",
        "th-text-secondary": "var(--color-text-secondary)",
        "th-text-muted": "var(--color-text-muted)",
        "th-border": "var(--color-border)",
        "th-border-subtle": "var(--color-border-subtle)",
        "th-input": "var(--color-input-bg)",
        "th-accent": "var(--color-accent)",
        "th-accent-hover": "var(--color-accent-hover)",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      keyframes: {
        "slide-in-right": {
          from: { transform: "translateX(100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "slide-in-left": {
          from: { transform: "translateX(-100%)", opacity: "0" },
          to: { transform: "translateX(0)", opacity: "1" },
        },
        "fade-in": {
          from: { opacity: "0" },
          to: { opacity: "1" },
        },
        "fade-in-up": {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        "slide-in-right": "slide-in-right 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        "slide-in-left": "slide-in-left 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
        "fade-in": "fade-in 0.2s ease-out",
        "fade-in-up": "fade-in-up 0.3s ease-out",
        shimmer: "shimmer 2s infinite linear",
      },
    },
  },
  plugins: [],
};

export default config;
