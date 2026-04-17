import Link from "next/link";
import { Mascot } from "@/components/fun/Mascot";
import { Button } from "@/components/ui/button";
import { Header } from "@/components/ui/header-2";
import { Footer } from "@/components/layout/Footer";

export default function NotFound() {
  return (
    <>
      <Header />
      <main className="container flex-1 grid place-items-center py-24">
        <div className="text-center space-y-5 max-w-md">
          <Mascot mood="sleeping" size={96} />
          <h1 className="text-6xl font-semibold tracking-tight text-gradient">404</h1>
          <p className="text-muted-foreground">La mascotte s'est endormie et a perdu la page. Désolé.</p>
          <Link href="/">
            <Button>Retour à l'accueil</Button>
          </Link>
        </div>
      </main>
      <Footer />
    </>
  );
}
