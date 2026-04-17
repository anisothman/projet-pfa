import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Header } from "@/components/ui/header-2";
import { Footer } from "@/components/layout/Footer";
import { SplineHero } from "@/components/spline/SplineHero";
import { Mascot } from "@/components/fun/Mascot";
import { Search, Brain, FileDown, Sparkles } from "lucide-react";

export default function LandingPage() {
  return (
    <>
      <Header />

      <main>
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 grid-pattern opacity-40 [mask-image:radial-gradient(ellipse_at_top,black,transparent_70%)]" />
          <div className="container relative pt-20 pb-16 md:pt-28 md:pb-20">
            <div className="grid gap-10 lg:grid-cols-2 items-center">
              <div className="space-y-6">
                <Badge variant="muted" className="gap-1">
                  <Sparkles className="h-3 w-3" /> fait par des étudiants, servi avec soin
                </Badge>
                <h1 className="text-5xl md:text-7xl font-semibold tracking-tight text-gradient leading-[1.05]">
                  Espionnez n'importe quelle entreprise.
                  <br />
                  <span className="font-serif italic accent-gradient">Recevez le dossier</span> en 30s.
                </h1>
                <p className="text-lg text-muted-foreground max-w-xl">
                  Donnez-nous un nom d'entreprise. On interroge Google, on fait raconter les détails à une IA,
                  et vous recevez un SWOT, un plan d'action et un joli PDF — plus vite que vous ne dites
                  "intelligence stratégique".
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <Link href="/analyze">
                    <Button size="lg" className="group">
                      Commencer l'analyse
                      <Search className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                    </Button>
                  </Link>
                  <Link href="/about">
                    <Button size="lg" variant="ghost">Voir l'équipe</Button>
                  </Link>
                </div>
                <div className="flex items-center gap-3 text-sm text-muted-foreground pt-2">
                  <Mascot mood="happy" size={32} />
                  <span>Pas d'inscription. Pas de pistage. Juste de l'analyse d'entreprises qui marche.</span>
                </div>
              </div>

              <div className="relative">
                <SplineHero />
              </div>
            </div>
          </div>
        </section>

        {/* Fonctionnalités */}
        <section className="container py-20">
          <div className="text-center mb-14">
            <h2 className="text-3xl md:text-4xl font-semibold tracking-tight">Trois étapes. Zéro blabla.</h2>
            <p className="text-muted-foreground mt-3 max-w-xl mx-auto">
              Ce qui était un script Python de 600 lignes est devenu un flux en un clic.
            </p>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            <Feature
              icon={<Search className="h-5 w-5" />}
              title="1. Collecter"
              body="On récupère les résultats Google, les avis, les notes et le knowledge graph de l'entreprise ciblée. 30 secondes, sans copier-coller."
            />
            <Feature
              icon={<Brain className="h-5 w-5" />}
              title="2. Analyser"
              body="GPT-4o-mini et Gemini, avec bascule automatique quand l'un atteint son quota. Fini les analyses interrompues en plein milieu."
            />
            <Feature
              icon={<FileDown className="h-5 w-5" />}
              title="3. Rapporter"
              body="SWOT et plan d'action rendus en PDF soigné. Plus une version web interactive avec timeline et KPIs."
            />
          </div>
        </section>

        {/* Clin d'œil */}
        <section className="container pb-24">
          <Card className="p-10 md:p-14 text-center relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 via-transparent to-transparent" />
            <div className="relative space-y-4">
              <Mascot mood="idle" size={56} />
              <h3 className="text-2xl md:text-3xl font-semibold tracking-tight">
                Psst — il y a un <span className="font-serif italic">code Konami</span> caché ici.
              </h3>
              <p className="text-muted-foreground max-w-lg mx-auto">
                Essayez ↑ ↑ ↓ ↓ ← → ← → B A. Ou pas. On vous laisse choisir.
              </p>
            </div>
          </Card>
        </section>
      </main>

      <Footer />
    </>
  );
}

function Feature({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <Card className="p-6 hover:-translate-y-0.5 hover:shadow-lg transition-all group">
      <div className="h-10 w-10 rounded-xl bg-primary/10 text-primary grid place-items-center mb-4 group-hover:bg-primary/20 transition-colors">
        {icon}
      </div>
      <div className="text-lg font-semibold mb-1">{title}</div>
      <p className="text-sm text-muted-foreground">{body}</p>
    </Card>
  );
}
