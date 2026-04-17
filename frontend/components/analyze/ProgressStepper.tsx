"use client";

import { motion } from "framer-motion";
import { Check, Loader2 } from "lucide-react";
import type { ProgressStage } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Step {
  key: ProgressStage;
  label: string;
}

const STEPS: Step[] = [
  { key: "serp_done", label: "Interrogation de Google…" },
  { key: "diagnostic_done", label: "Génération du SWOT…" },
  { key: "plan_done", label: "Plan d'action…" },
  { key: "pdf_ready", label: "Rapport prêt" },
];

const REACHED_ORDER: ProgressStage[] = [
  "queued",
  "serp_started", "serp_done",
  "diagnostic_started", "diagnostic_done",
  "plan_started", "plan_done",
  "pdf_ready",
];

function hasReached(current: ProgressStage, target: ProgressStage): boolean {
  return REACHED_ORDER.indexOf(current) >= REACHED_ORDER.indexOf(target);
}

export function ProgressStepper({ stage }: { stage: ProgressStage }) {
  return (
    <ol className="space-y-4">
      {STEPS.map((s, i) => {
        const done = hasReached(stage, s.key);
        const active = !done && REACHED_ORDER.indexOf(stage) >= REACHED_ORDER.indexOf(s.key) - 1;
        return (
          <motion.li
            key={s.key}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.04 }}
            className={cn(
              "flex items-center gap-3 text-sm",
              done ? "text-foreground" : active ? "text-foreground" : "text-muted-foreground/60",
            )}
          >
            <div
              className={cn(
                "h-7 w-7 shrink-0 rounded-full grid place-items-center border",
                done
                  ? "bg-primary/15 border-primary/40 text-primary"
                  : active
                    ? "border-primary/60 text-primary"
                    : "border-border",
              )}
            >
              {done ? <Check className="h-4 w-4" /> : active ? <Loader2 className="h-4 w-4 animate-spin" /> : i + 1}
            </div>
            <span>{s.label}</span>
          </motion.li>
        );
      })}
    </ol>
  );
}
