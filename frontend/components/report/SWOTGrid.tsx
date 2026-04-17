"use client";

import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { DiagnosticItem } from "@/lib/types";
import { cn } from "@/lib/utils";

interface Quadrant {
  key: string;
  title: string;
  items: DiagnosticItem[];
  tone: "success" | "danger" | "default" | "warn";
}

export function SWOTGrid({
  forces,
  faiblesses,
  opportunites,
  menaces,
}: {
  forces: DiagnosticItem[];
  faiblesses: DiagnosticItem[];
  opportunites: DiagnosticItem[];
  menaces: DiagnosticItem[];
}) {
  const quadrants: Quadrant[] = [
    { key: "forces", title: "Forces", items: forces, tone: "success" },
    { key: "faiblesses", title: "Faiblesses", items: faiblesses, tone: "danger" },
    { key: "opportunites", title: "Opportunités", items: opportunites, tone: "default" },
    { key: "menaces", title: "Menaces", items: menaces, tone: "warn" },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {quadrants.map((q, i) => (
        <motion.div
          key={q.key}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: i * 0.06 }}
        >
          <Card className={cn("p-5 h-full", toneRing[q.tone])}>
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-base font-semibold tracking-tight">{q.title}</h3>
              <Badge variant={q.tone}>{q.items.length}</Badge>
            </div>
            {q.items.length === 0 ? (
              <p className="text-sm text-muted-foreground italic">Rien à signaler.</p>
            ) : (
              <ul className="space-y-3">
                {q.items.map((it, idx) => (
                  <li key={idx} className="text-sm">
                    <div className="font-medium">{it.titre}</div>
                    <p className="text-muted-foreground mt-0.5">{it.description}</p>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        </motion.div>
      ))}
    </div>
  );
}

const toneRing: Record<Quadrant["tone"], string> = {
  success: "ring-1 ring-emerald-500/20",
  danger: "ring-1 ring-red-500/20",
  default: "ring-1 ring-primary/20",
  warn: "ring-1 ring-amber-500/20",
};
