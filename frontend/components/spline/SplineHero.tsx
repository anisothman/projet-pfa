"use client";

import { useRef, useState } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Star, TrendingUp, AlertTriangle, Lightbulb, Target, Sparkles } from "lucide-react";

type Sample = {
  name: string;
  tagline: string;
  rating: number;
  reviewCount: string;
  forces: string[];
  faiblesses: string[];
  opportunites: string[];
  menaces: string[];
};

const SAMPLES: Sample[] = [
  {
    name: "Samsung",
    tagline: "Électronique grand public",
    rating: 4.3,
    reviewCount: "48.2k avis",
    forces: ["Gamme Galaxy", "R&D puissante", "Écosystème"],
    faiblesses: ["Qualité SAV", "Prix premium"],
    opportunites: ["IA générative", "Marchés émergents"],
    menaces: ["Pression chinoise", "Cycles de stocks"],
  },
  {
    name: "Ooredoo Tunisie",
    tagline: "Télécommunications",
    rating: 3.9,
    reviewCount: "12.4k avis",
    forces: ["Couverture 5G", "Forfaits data", "Notoriété"],
    faiblesses: ["Temps d'attente", "App mobile"],
    opportunites: ["Fibre optique", "B2B PME"],
    menaces: ["Orange TN", "Régulation ARCEP"],
  },
  {
    name: "Café de la Paix",
    tagline: "Restauration · Tunis",
    rating: 4.6,
    reviewCount: "2.1k avis",
    forces: ["Terrasse vue mer", "Service", "Cuisine"],
    faiblesses: ["Pas de livraison", "Parking"],
    opportunites: ["Brunch week-end", "Événements privés"],
    menaces: ["Saison basse", "Nouveaux voisins"],
  },
];

export function SplineHero() {
  const [index, setIndex] = useState(0);
  const sample = SAMPLES[index];

  const ref = useRef<HTMLDivElement>(null);
  const mx = useMotionValue(0);
  const my = useMotionValue(0);
  const rotateX = useTransform(useSpring(my, { stiffness: 150, damping: 20 }), [-0.5, 0.5], [8, -8]);
  const rotateY = useTransform(useSpring(mx, { stiffness: 150, damping: 20 }), [-0.5, 0.5], [-12, 12]);

  function onMouseMove(e: React.MouseEvent<HTMLDivElement>) {
    const rect = ref.current?.getBoundingClientRect();
    if (!rect) return;
    mx.set((e.clientX - rect.left) / rect.width - 0.5);
    my.set((e.clientY - rect.top) / rect.height - 0.5);
  }
  function onMouseLeave() {
    mx.set(0);
    my.set(0);
  }

  return (
    <div
      ref={ref}
      onMouseMove={onMouseMove}
      onMouseLeave={onMouseLeave}
      className="relative h-[520px] w-full overflow-hidden rounded-3xl bg-gradient-to-br from-background via-background to-primary/5 [perspective:1400px]"
    >
      <div className="absolute inset-0 grid-pattern opacity-20 [mask-image:radial-gradient(ellipse_at_center,black,transparent_75%)]" />

      <motion.div
        className="pointer-events-none absolute h-[500px] w-[500px] -translate-x-1/2 -translate-y-1/2 rounded-full bg-primary/20 blur-3xl"
        style={{
          left: useTransform(mx, [-0.5, 0.5], ["30%", "70%"]),
          top: useTransform(my, [-0.5, 0.5], ["30%", "70%"]),
        }}
      />

      <div className="absolute top-5 left-1/2 -translate-x-1/2 z-20 flex gap-1 rounded-full border border-border bg-background/80 p-1 backdrop-blur">
        {SAMPLES.map((s, i) => (
          <button
            key={s.name}
            onClick={() => setIndex(i)}
            className={`relative rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              i === index ? "text-primary-foreground" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {i === index && (
              <motion.div
                layoutId="picker-pill"
                className="absolute inset-0 rounded-full bg-primary"
                transition={{ type: "spring", stiffness: 400, damping: 30 }}
              />
            )}
            <span className="relative z-10">{s.name}</span>
          </button>
        ))}
      </div>

      <motion.div
        style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
        className="absolute inset-0 flex items-center justify-center"
      >
        <AnimatePresence mode="wait">
          <motion.div
            key={sample.name}
            initial={{ opacity: 0, y: 12, rotateX: -8 }}
            animate={{ opacity: 1, y: 0, rotateX: 0 }}
            exit={{ opacity: 0, y: -12, rotateX: 8 }}
            transition={{ duration: 0.3 }}
            className="w-[86%] max-w-[500px] rounded-3xl border border-border bg-card/90 p-6 shadow-[0_40px_80px_-20px_rgba(124,58,237,0.35)] backdrop-blur-xl"
            style={{ transformStyle: "preserve-3d" }}
          >
            <div className="flex items-start justify-between" style={{ transform: "translateZ(40px)" }}>
              <div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <Sparkles className="h-3 w-3 text-primary" /> Rapport Localis AI
                </div>
                <div className="mt-1 text-2xl font-semibold tracking-tight">{sample.name}</div>
                <div className="text-xs text-muted-foreground">{sample.tagline}</div>
              </div>
              <div className="text-right">
                <div className="flex items-center gap-1 font-semibold text-amber-500">
                  <Star className="h-4 w-4 fill-current" />
                  {sample.rating.toFixed(1)}
                </div>
                <div className="text-[10px] text-muted-foreground">{sample.reviewCount}</div>
              </div>
            </div>

            <div className="mt-5 grid grid-cols-2 gap-2" style={{ transform: "translateZ(30px)" }}>
              <Quad
                icon={<TrendingUp className="h-3.5 w-3.5" />}
                title="Forces"
                tone="emerald"
                items={sample.forces}
              />
              <Quad
                icon={<AlertTriangle className="h-3.5 w-3.5" />}
                title="Faiblesses"
                tone="red"
                items={sample.faiblesses}
              />
              <Quad
                icon={<Lightbulb className="h-3.5 w-3.5" />}
                title="Opportunités"
                tone="violet"
                items={sample.opportunites}
              />
              <Quad
                icon={<Target className="h-3.5 w-3.5" />}
                title="Menaces"
                tone="amber"
                items={sample.menaces}
              />
            </div>

            {/* Barre de pied */}
            <div
              className="mt-5 flex items-center justify-between rounded-xl border border-border bg-background/50 p-3 text-xs"
              style={{ transform: "translateZ(20px)" }}
            >
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                  <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
                </span>
                <span className="text-muted-foreground">Analyse live</span>
              </div>
              <div className="text-muted-foreground">
                gpt-4o-mini · <span className="text-emerald-500">PDF prêt</span>
              </div>
            </div>
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* Indication */}
      <div className="pointer-events-none absolute bottom-4 left-1/2 -translate-x-1/2 text-[10px] uppercase tracking-widest text-muted-foreground/60">
        bouge la souris · change d'entreprise
      </div>
    </div>
  );
}

function Quad({
  icon,
  title,
  tone,
  items,
}: {
  icon: React.ReactNode;
  title: string;
  tone: "emerald" | "red" | "violet" | "amber";
  items: string[];
}) {
  const toneMap = {
    emerald: "text-emerald-500 bg-emerald-500/10 ring-emerald-500/20",
    red: "text-red-500 bg-red-500/10 ring-red-500/20",
    violet: "text-violet-500 bg-violet-500/10 ring-violet-500/20",
    amber: "text-amber-500 bg-amber-500/10 ring-amber-500/20",
  };

  return (
    <motion.div
      whileHover={{ scale: 1.03 }}
      transition={{ type: "spring", stiffness: 400, damping: 25 }}
      className="rounded-xl border border-border bg-background/40 p-3"
    >
      <div
        className={`inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[10px] font-medium ring-1 ${toneMap[tone]}`}
      >
        {icon}
        {title}
      </div>
      <ul className="mt-2 space-y-1">
        {items.map((it, i) => (
          <motion.li
            key={`${title}-${i}-${it}`}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.05 * i + 0.1 }}
            className="truncate text-[11px] text-foreground"
          >
            · {it}
          </motion.li>
        ))}
      </ul>
    </motion.div>
  );
}
