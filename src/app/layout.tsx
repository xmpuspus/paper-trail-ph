import type { Metadata } from "next";
import { Archivo, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/common/ThemeProvider";

const display = Archivo({
  subsets: ["latin"],
  weight: ["500", "600", "700", "800"],
  variable: "--font-display",
  display: "swap",
});

const body = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
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
  title: "Paper Trail PH: the flood-control money, mapped",
  description:
    "An interactive graph of DPWH flood-control contracts, the firms that won them, and the official actions and cases on record. Statistical indicators from public records, not accusations.",
  keywords:
    "philippines, DPWH, flood control, procurement, transparency, accountability, contractors, PhilGEPS, corruption, public records",
  openGraph: {
    title: "Paper Trail PH: the flood-control money, mapped",
    description:
      "Follow PHP 1.586 trillion in DPWH flood-control contracts across 33,866 projects and the firms that won them.",
    type: "website",
  },
};

// Set the theme before paint to avoid a flash of the wrong mode.
const noFlash = `(function(){try{var t=localStorage.getItem('paper-trail-theme')||'dark';document.documentElement.setAttribute('data-theme',t);}catch(e){document.documentElement.setAttribute('data-theme','dark');}})();`;

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" data-theme="dark">
      <head>
        <script dangerouslySetInnerHTML={{ __html: noFlash }} />
      </head>
      <body className={`${display.variable} ${body.variable} ${mono.variable}`}>
        <a href="#main" className="skip-link">Skip to content</a>
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}
