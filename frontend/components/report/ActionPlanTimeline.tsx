"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { Action, ActionPlan } from "@/lib/types";
import { cn } from "@/lib/utils";

interface HorizonProps {
  title: string;
  subtitle: string;
  actions: Action[];
  color: string;
  index: number;
}

function Horizon({ title, subtitle, actions, color, index }: HorizonProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.06 }}
    >
      <div className="flex items-center gap-3 mb-4">
        <div className={cn("h-3 w-3 rounded-full", color)} />
        <div>
          <div className="font-semibold">{title}</div>
          <div className="text-xs text-muted-foreground">{subtitle}</div>
        </div>
      </div>
      <div className="space-y-2 pl-6 border-l border-border">
        {actions.length === 0 && <p className="text-sm text-muted-foreground italic">Aucune action.</p>}
        {actions.map((a, i) => (
          <Card key={i} className="p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="space-y-1">
                <div className="font-medium text-sm">{a.action}</div>
                <p className="text-sm text-muted-foreground">{a.description}</p>
              </div>
              {a.priorite && (
                <Badge variant={prioVariant(a.priorite)} className="shrink-0">
                  {a.priorite}
                </Badge>
              )}
            </div>
            {(a.delai_jours || a.delai_mois) && (
              <div className="mt-2 text-xs text-muted-foreground">
                {a.delai_jours ? `${a.delai_jours} jours` : `${a.delai_mois} mois`}
              </div>
            )}
          </Card>
        ))}
      </div>
    </motion.div>
  );
}

function prioVariant(p: string): "danger" | "warn" | "default" | "muted" {
  return p === "P0" ? "danger" : p === "P1" ? "warn" : p === "P2" ? "default" : "muted";
}

export function ActionPlanTimeline({ plan }: { plan: ActionPlan }) {
  return (
    <div className="space-y-8">
      {plan.resume_executif && (
        <Card className="p-5 bg-primary/5 border-primary/20">
          <div className="text-xs uppercase tracking-wide text-primary mb-2">Résumé exécutif</div>
          <p className="text-sm">{plan.resume_executif}</p>
        </Card>
      )}
      <div className="grid gap-10 md:grid-cols-3">
        <Horizon title="Court terme" subtitle="0 – 3 mois" actions={plan.court_terme} color="bg-red-500" index={0} />
        <Horizon title="Moyen terme" subtitle="3 – 6 mois" actions={plan.moyen_terme} color="bg-amber-500" index={1} />
        <Horizon title="Long terme" subtitle="6 – 12 mois" actions={plan.long_terme} color="bg-emerald-500" index={2} />
      </div>
    </div>
  );
}
