import type { Metadata } from "next";
import { Libre_Franklin, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/common/ThemeProvider";

// Libre Franklin: a Franklin Gothic revival, the lineage of American
// newspaper headlines and US civic design. Newsroom gravitas, not startup gloss.
const sans = Libre_Franklin({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-body",
  display: "swap",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Paper Trail PH: DPWH flood-control contracts as a graph",
  description:
    "An interactive graph of DPWH flood-control contracts, the firms that won them, and the official actions and cases on record, linked to their sources. Not accusations, but statistical indicators from public records.",
  keywords:
    "philippines, DPWH, flood control, procurement, transparency, accountability, contractors, PhilGEPS, public records",
  openGraph: {
    title: "Paper Trail PH: DPWH flood-control contracts as a graph",
    description:
      "PHP 1.586 trillion in DPWH flood-control contracts across 33,866 projects, and the firms that won them.",
    type: "website",
  },
};

const noFlash = `(function(){try{var t=localStorage.getItem('paper-trail-theme')||'light';document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','light');}})();`;

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="light">
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlash }} />
      </head>
      <body className={`${sans.variable} ${mono.variable}`}>
        <a href="#main" className="skip-link">Skip to content</a>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
