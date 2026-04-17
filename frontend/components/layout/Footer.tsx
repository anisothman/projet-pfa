import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-border/60 mt-24">
      <div className="container py-12 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 text-sm text-muted-foreground">
        <div className="space-y-1">
          <div className="text-foreground font-medium">Localis AI</div>
          <div>Projet de fin d'année — Maram, Anis, Isra, Hiba, Tasnim, Nourhene</div>
          <div className="text-xs">Construit avec Next.js et FastAPI. Pas de pub, pas de pistage, juste du code.</div>
        </div>
        <div className="flex items-center gap-5">
          <Link href="/about" className="hover:text-foreground transition-colors">L'équipe</Link>
        </div>
      </div>
    </footer>
  );
}
