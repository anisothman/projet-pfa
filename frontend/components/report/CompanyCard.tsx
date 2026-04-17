import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Company } from "@/lib/types";
import { Star, MapPin, Phone, Globe } from "lucide-react";

export function CompanyCard({ company }: { company: Company }) {
  return (
    <Card className="p-6 md:p-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="space-y-2">
          <h1 className="text-3xl md:text-4xl font-semibold tracking-tight">{company.nom}</h1>
          {company.categorie && <Badge variant="muted">{company.categorie}</Badge>}
        </div>
        {company.note_moyenne != null && (
          <div className="text-right">
            <div className="flex items-center gap-1 text-amber-500 font-semibold">
              <Star className="h-4 w-4 fill-current" />
              {company.note_moyenne.toFixed(1)}
              <span className="text-muted-foreground text-sm font-normal">/ 5</span>
            </div>
            {company.nombre_avis != null && (
              <div className="text-xs text-muted-foreground">{company.nombre_avis} avis</div>
            )}
          </div>
        )}
      </div>

      <div className="grid gap-3 md:grid-cols-3 mt-6 text-sm">
        <Row icon={<MapPin className="h-4 w-4" />}>{company.adresse}</Row>
        <Row icon={<Phone className="h-4 w-4" />}>{company.telephone ?? "—"}</Row>
        <Row icon={<Globe className="h-4 w-4" />}>
          {company.site_web ? (
            <a href={company.site_web} target="_blank" rel="noreferrer" className="underline">
              {company.site_web.replace(/^https?:\/\//, "")}
            </a>
          ) : (
            "—"
          )}
        </Row>
      </div>
    </Card>
  );
}

function Row({ icon, children }: { icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-muted-foreground mt-0.5">{icon}</span>
      <span className="text-muted-foreground">{children}</span>
    </div>
  );
}
