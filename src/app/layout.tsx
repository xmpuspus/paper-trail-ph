import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import { DISCLAIMER } from "@/lib/constants";
import { ThemeProvider } from "@/components/common/ThemeProvider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-jetbrains-mono",
});

export const metadata: Metadata = {
  title: "Paper Trail PH | Philippine Public Accountability Graph",
  description: "Follow the paper trail — visualize procurement, political connections, and red flags in Philippine public spending",
  keywords: "philippines, procurement, transparency, accountability, government, contracts, philgeps",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${jetbrainsMono.variable} font-sans`}>
        <ThemeProvider>
          <DisclaimerBanner />
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}

function DisclaimerBanner() {
  return (
    <div
      className="fixed top-0 left-0 right-0 z-[60] backdrop-blur-md"
      style={{
        backgroundColor: "var(--glass-bg)",
        borderBottom: "1px solid var(--color-border)",
      }}
    >
      <div
        className="px-4 py-1.5 text-center text-[11px] tracking-wide"
        style={{ color: "var(--color-text-muted)" }}
      >
        {DISCLAIMER}
      </div>
    </div>
  );
}
