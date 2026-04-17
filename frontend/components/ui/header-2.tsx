"use client";
import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button, buttonVariants } from "@/components/ui/button";
import { MenuToggleIcon } from "@/components/ui/menu-toggle-icon";
import { useScroll } from "@/components/ui/use-scroll";
import { Mascot } from "@/components/fun/Mascot";
import { cn } from "@/lib/utils";

export function Header() {
  const [open, setOpen] = React.useState(false);
  const scrolled = useScroll(10);
  const pathname = usePathname();
  const showHome = pathname !== "/";
  const showStart = pathname !== "/analyze";

  const links = [{ label: "L'équipe", href: "/about" }].filter((l) => l.href !== pathname);

  React.useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  const closeMenu = () => setOpen(false);

  return (
    <header
      className={cn(
        "sticky top-0 z-50 mx-auto w-full max-w-6xl border-b border-transparent md:rounded-2xl md:border md:transition-all md:ease-out",
        {
          "bg-background/95 supports-[backdrop-filter]:bg-background/60 border-border backdrop-blur-lg md:top-4 md:max-w-5xl md:shadow-lg":
            scrolled && !open,
          "bg-background/90": open,
        },
      )}
    >
      <nav
        className={cn(
          "flex h-20 w-full items-center justify-between px-6 md:h-16 md:px-5 md:transition-all md:ease-out",
          { "md:px-4": scrolled },
        )}
      >
        <Link href="/" className="flex items-center gap-3 text-xl font-semibold" onClick={closeMenu}>
          <Mascot size={36} />
          <span className="tracking-tight">Localis</span>
          <span className="ml-0.5 text-sm text-muted-foreground">AI</span>
        </Link>

        <div className="hidden items-center gap-2 md:flex">
          {links.map((link) => (
            <Link
              key={link.href}
              className={cn(buttonVariants({ variant: "ghost" }), "text-base px-5")}
              href={link.href}
            >
              {link.label}
            </Link>
          ))}
          {showHome && (
            <Link href="/">
              <Button size="lg" variant="outline" className="text-base">Accueil</Button>
            </Link>
          )}
          {showStart && (
            <Link href="/analyze">
              <Button size="lg" className="text-base">Commencer</Button>
            </Link>
          )}
        </div>

        <Button
          size="icon"
          variant="outline"
          onClick={() => setOpen(!open)}
          className="md:hidden h-12 w-12"
          aria-label={open ? "Fermer le menu" : "Ouvrir le menu"}
        >
          <MenuToggleIcon open={open} className="size-6" duration={300} />
        </Button>
      </nav>

      <div
        className={cn(
          "bg-background/90 fixed top-20 right-0 bottom-0 left-0 z-50 flex flex-col overflow-hidden border-y md:hidden",
          open ? "block" : "hidden",
        )}
      >
        <div
          data-slot={open ? "open" : "closed"}
          className={cn(
            "data-[slot=open]:animate-in data-[slot=open]:zoom-in-95 data-[slot=closed]:animate-out data-[slot=closed]:zoom-out-95 ease-out",
            "flex h-full w-full flex-col justify-between gap-y-2 p-4",
          )}
        >
          <div className="grid gap-y-3">
            {links.map((link) => (
              <Link
                key={link.href}
                className={cn(
                  buttonVariants({ variant: "ghost", size: "lg" }),
                  "justify-start text-lg",
                )}
                href={link.href}
                onClick={closeMenu}
              >
                {link.label}
              </Link>
            ))}
          </div>
          <div className="flex flex-col gap-2">
            {showHome && (
              <Link href="/" onClick={closeMenu}>
                <Button size="lg" variant="outline" className="w-full text-base">Accueil</Button>
              </Link>
            )}
            {showStart && (
              <Link href="/analyze" onClick={closeMenu}>
                <Button size="lg" className="w-full text-base">Commencer</Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
