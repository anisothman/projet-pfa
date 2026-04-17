import { Header } from "@/components/ui/header-2";
import { Footer } from "@/components/layout/Footer";
import { Card } from "@/components/ui/card";
import { Mascot } from "@/components/fun/Mascot";

const TEAM = [
  { name: "Maram", role: "Orchestration IA (Sprint 2)" },
  { name: "Anis", role: "Collecte SerpAPI (Sprint 1)" },
  { name: "Isra", role: "Prompt engineering" },
  { name: "Hiba", role: "Nettoyage / parsing" },
  { name: "Tasnim", role: "Schémas de données" },
  { name: "Nourhene", role: "Rapport PDF (Sprint 3)" },
];

export default function AboutPage() {
  return (
    <>
      <Header />
      <main className="container py-16 space-y-12">
        <header className="max-w-2xl space-y-4">
          <div className="flex items-center gap-3">
            <Mascot mood="happy" size={48} />
            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-gradient">
              Fait avec <span className="font-serif italic accent-gradient">beaucoup</span> de café.
            </h1>
          </div>
          <p className="text-muted-foreground">
            Localis AI est un projet de fin d'année. Six étudiants, trois sprints, une quantité déraisonnable de
            threads Slack. Pas de modèle économique, pas de CEO, pas de pitch deck. Juste du code, un LLM, et
            l'envie de voir si "business intelligence" peut être amusant.
          </p>
        </header>

        <section>
          <h2 className="text-2xl font-semibold tracking-tight mb-6">L'équipe</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {TEAM.map((m) => (
              <Card key={m.name} className="p-5">
                <div className="font-medium">{m.name}</div>
                <div className="text-sm text-muted-foreground mt-0.5">{m.role}</div>
              </Card>
            ))}
          </div>
        </section>

      </main>
      <Footer />
    </>
  );
}
