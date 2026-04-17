import { notFound } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/ui/header-2";
import { Footer } from "@/components/layout/Footer";
import { SWOTGrid } from "@/components/report/SWOTGrid";
import { ActionPlanTimeline } from "@/components/report/ActionPlanTimeline";
import { CompanyCard } from "@/components/report/CompanyCard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ConfettiOnMount } from "@/components/fun/ConfettiOnMount";
import { ShareButton } from "./ShareButton";
import { fetchReport, reportPdfUrl } from "@/lib/api";
import { Download } from "lucide-react";

interface Props {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ fromAnalyze?: string }>;
}

export default async function ReportPage({ params, searchParams }: Props) {
  const { id } = await params;
  const { fromAnalyze } = await searchParams;
  const report = await fetchReport(id);
  if (!report) notFound();

  return (
    <>
      <Header />
      {fromAnalyze === "1" && <ConfettiOnMount />}
      <main className="container py-12 space-y-10">
        <div className="flex items-center justify-between">
          <Link href="/analyze" className="text-sm text-muted-foreground hover:text-foreground">
            ← Nouvelle analyse
          </Link>
          <div className="flex items-center gap-2">
            <ShareButton />
            <a href={reportPdfUrl(id)} target="_blank" rel="noreferrer">
              <Button>
                <Download className="h-4 w-4" /> Télécharger PDF
              </Button>
            </a>
          </div>
        </div>

        <CompanyCard company={report.entreprise} />

        <section>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-2xl font-semibold tracking-tight">Analyse SWOT</h2>
            {report.metadonnees.provider && (
              <Badge variant="muted">
                {report.metadonnees.provider} · {report.metadonnees.modele}
              </Badge>
            )}
          </div>
          <SWOTGrid
            forces={report.diagnostic.points_forts}
            faiblesses={report.diagnostic.points_faibles}
            opportunites={report.diagnostic.opportunites}
            menaces={report.diagnostic.menaces}
          />
        </section>

        <section>
          <h2 className="text-2xl font-semibold tracking-tight mb-6">Plan d'action</h2>
          <ActionPlanTimeline plan={report.plan_action} />
        </section>

        {report.plan_action.kpis && report.plan_action.kpis.length > 0 && (
          <section>
            <h2 className="text-2xl font-semibold tracking-tight mb-4">KPIs à suivre</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-muted-foreground border-b border-border">
                  <tr>
                    <th className="py-2 pr-4">Métrique</th>
                    <th className="py-2 pr-4">Baseline</th>
                    <th className="py-2 pr-4">Cible</th>
                    <th className="py-2">Fréquence</th>
                  </tr>
                </thead>
                <tbody>
                  {report.plan_action.kpis.map((k, i) => (
                    <tr key={i} className="border-b border-border/50">
                      <td className="py-3 pr-4 font-medium">{k.metrique}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{String(k.baseline ?? "—")}</td>
                      <td className="py-3 pr-4 text-muted-foreground">{String(k.cible ?? "—")}</td>
                      <td className="py-3 text-muted-foreground">{k.frequence_mesure ?? "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </main>
      <Footer />
    </>
  );
}
