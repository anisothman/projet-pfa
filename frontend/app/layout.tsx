import type { Metadata } from "next";
import { Geist, Geist_Mono, Instrument_Serif } from "next/font/google";
import "./globals.css";
import { EasterEgg } from "@/components/fun/EasterEgg";

const geistSans = Geist({ subsets: ["latin"], variable: "--font-geist-sans" });
const geistMono = Geist_Mono({ subsets: ["latin"], variable: "--font-geist-mono" });
const instrumentSerif = Instrument_Serif({
  subsets: ["latin"],
  weight: "400",
  variable: "--font-instrument-serif",
});

export const metadata: Metadata = {
  title: "Localis AI — espionnez n'importe quelle entreprise",
  description:
    "Donnez-nous un nom d'entreprise, on interroge Google pour vous et on revient avec un SWOT, un plan d'action et un PDF impeccable.",
  openGraph: {
    title: "Localis AI",
    description: "Espionnez n'importe quelle entreprise. Recevez le dossier en 30s.",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr" className="dark" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} ${instrumentSerif.variable} font-sans min-h-screen bg-background text-foreground`}
      >
        {children}
        <EasterEgg />
      </body>
    </html>
  );
}
