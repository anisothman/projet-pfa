"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Header } from "@/components/ui/header-2";
import { Footer } from "@/components/layout/Footer";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Mascot } from "@/components/fun/Mascot";
import { ProgressStepper } from "@/components/analyze/ProgressStepper";
import { analyzeStream, fetchCandidates } from "@/lib/api";
import { addRecent, clearRecent, getRecent, type RecentEntry } from "@/lib/recent";
import { useDebounced } from "@/lib/useDebounced";
import type { Candidate, ProgressEvent, ProgressStage } from "@/lib/types";
import {
  Building2,
  ExternalLink,
  History,
  Loader2,
  MapPin,
  Phone,
  Search,
  Star,
  Trash2,
} from "lucide-react";

type Mode = "search" | "analyzing";

export default function AnalyzePage() {
  const router = useRouter();
  const [mode, setMode] = useState<Mode>("search");

  const [company, setCompany] = useState("");
  const [city, setCity] = useState("");
  const debouncedCompany = useDebounced(company, 400);
  const debouncedCity = useDebounced(city, 400);

  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  const [stage, setStage] = useState<ProgressStage>("queued");
  const [message, setMessage] = useState<string>("");
  const [analyzeError, setAnalyzeError] = useState<string | null>(null);
  const [selectedTitle, setSelectedTitle] = useState<string>("");

  const [recent, setRecent] = useState<RecentEntry[]>([]);
  const searchAbortRef = useRef<AbortController | null>(null);
  const analyzeAbortRef = useRef<AbortController | null>(null);

  useEffect(() => setRecent(getRecent()), []);
  useEffect(
    () => () => {
      searchAbortRef.current?.abort();
      analyzeAbortRef.current?.abort();
    },
    [],
  );

  // Recherche en direct : se déclenche à chaque changement debouncé du nom/ville.
  useEffect(() => {
    if (mode !== "search") return;
    const name = debouncedCompany.trim();
    if (name.length < 2) {
      setCandidates([]);
      setSearching(false);
      setSearchError(null);
      setHasSearched(false);
      return;
    }
    const location = debouncedCity.trim() || null;

    searchAbortRef.current?.abort();
    const ctrl = new AbortController();
    searchAbortRef.current = ctrl;

    setSearching(true);
    setSearchError(null);

    fetchCandidates(name, location, ctrl.signal)
      .then((resp) => {
        if (ctrl.signal.aborted) return;
        setCandidates(resp.candidates);
        setHasSearched(true);
      })
      .catch((e: Error) => {
        if (e.name === "AbortError") return;
        setSearchError(e.message);
      })
      .finally(() => {
        if (!ctrl.signal.aborted) setSearching(false);
      });
  }, [debouncedCompany, debouncedCity, mode]);

  const runAnalysis = useCallback(
    async (candidate: Candidate) => {
      setMode("analyzing");
      setSelectedTitle(candidate.title);
      setAnalyzeError(null);
      setStage("queued");
      setMessage("Démarrage…");

      const ctrl = new AbortController();
      analyzeAbortRef.current = ctrl;

      try {
        await analyzeStream(
          candidate.title,
          city.trim() || null,
          (evt: ProgressEvent) => {
            setStage(evt.stage);
            setMessage(evt.message);
            if (evt.stage === "pdf_ready" && evt.report_id) {
              addRecent({ id: evt.report_id, company: candidate.title, ts: Date.now() });
              router.push(`/report/${evt.report_id}?fromAnalyze=1`);
            }
            if (evt.stage === "error") {
              setAnalyzeError(evt.message);
            }
          },
          ctrl.signal,
        );
      } catch (e) {
        if ((e as Error).name !== "AbortError") setAnalyzeError(String((e as Error).message));
      }
    },
    [city, router],
  );

  const backToSearch = () => {
    analyzeAbortRef.current?.abort();
    setMode("search");
    setAnalyzeError(null);
    setStage("queued");
    setMessage("");
  };

  return (
    <>
      <Header />
      <main className="container py-14">
        <div className="max-w-3xl mx-auto space-y-8">
          <header className="text-center space-y-3">
            <div className="flex justify-center">
              <Mascot mood={mode === "analyzing" ? "thinking" : "idle"} size={56} />
            </div>
            <h1 className="text-4xl md:text-5xl font-semibold tracking-tight text-gradient">
              Qui voulez-vous <span className="font-serif italic accent-gradient">espionner</span> ?
            </h1>
            <p className="text-muted-foreground">
              {mode === "analyzing"
                ? `Analyse de « ${selectedTitle} »`
                : "Tapez un nom — la recherche se lance en direct. Cliquez sur l'entreprise à analyser."}
            </p>
          </header>

          {mode === "search" ? (
            <>
              <Card className="p-6 md:p-8 space-y-5">
                <div className="grid gap-3 sm:grid-cols-[2fr_1fr]">
                  <LabeledInput
                    icon={<Building2 className="h-4 w-4" />}
                    label="Entreprise"
                    placeholder="Samsung, KFC, Café de la Paix…"
                    value={company}
                    onChange={setCompany}
                    autoFocus
                  />
                  <LabeledInput
                    icon={<MapPin className="h-4 w-4" />}
                    label="Ville"
                    placeholder="Tunis, Paris… (optionnel)"
                    value={city}
                    onChange={setCity}
                  />
                </div>

                <SearchStatus
                  companyLen={debouncedCompany.trim().length}
                  searching={searching}
                  hasSearched={hasSearched}
                  candidatesCount={candidates.length}
                  error={searchError}
                />

                {candidates.length > 0 && (
                  <div className="space-y-2">
                    {candidates.map((c) => (
                      <CandidateButton key={c.id} candidate={c} onPick={runAnalysis} />
                    ))}
                  </div>
                )}
              </Card>

              {recent.length > 0 && (
                <section className="space-y-3">
                  <div className="flex items-center justify-between text-sm text-muted-foreground">
                    <div className="flex items-center gap-2">
                      <History className="h-4 w-4" /> Vos derniers espionnages
                    </div>
                    <button
                      type="button"
                      onClick={() => {
                        clearRecent();
                        setRecent([]);
                      }}
                      className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs hover:text-foreground hover:bg-secondary transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" /> Effacer
                    </button>
                  </div>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {recent.map((r) => (
                      <Link key={r.id} href={`/report/${r.id}`}>
                        <Card className="p-4 hover:border-primary/50 transition-colors">
                          <div className="font-medium truncate">{r.company}</div>
                          <div className="text-xs text-muted-foreground">
                            {new Date(r.ts).toLocaleString("fr-FR")}
                          </div>
                        </Card>
                      </Link>
                    ))}
                  </div>
                </section>
              )}
            </>
          ) : (
            <Card className="p-6 md:p-8 space-y-6">
              <div className="space-y-6">
                <div className="text-sm text-muted-foreground">
                  {message || "Démarrage…"}
                  <span className="ml-1 inline-block animate-pulse">·</span>
                </div>
                <ProgressStepper stage={stage} />
                <p className="text-xs text-muted-foreground">
                  La génération peut prendre jusqu'à 40 secondes.
                </p>
              </div>

              {analyzeError && (
                <div>
                  <ErrorBanner message={analyzeError} />
                  <Button variant="outline" onClick={backToSearch} className="mt-3">
                    Retour à la recherche
                  </Button>
                </div>
              )}
            </Card>
          )}
        </div>
      </main>
      <Footer />
    </>
  );
}

function CandidateButton({ candidate, onPick }: { candidate: Candidate; onPick: (c: Candidate) => void }) {
  const hasPlaceData = Boolean(candidate.address || candidate.rating || candidate.phone);
  return (
    <button onClick={() => onPick(candidate)} className="group block w-full text-left">
      <div className="flex items-start justify-between gap-3 rounded-xl border border-border bg-background/40 p-4 transition-all hover:border-primary/60 hover:bg-primary/5">
        <div className="min-w-0 flex-1 space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="font-medium truncate">{candidate.title}</span>
            {candidate.rating != null && (
              <span className="inline-flex shrink-0 items-center gap-0.5 text-xs font-medium text-amber-500">
                <Star className="h-3 w-3 fill-current" />
                {candidate.rating.toFixed(1)}
                {candidate.reviews != null && (
                  <span className="ml-1 font-normal text-muted-foreground">({candidate.reviews})</span>
                )}
              </span>
            )}
          </div>
          {candidate.place_type && (
            <div className="text-xs uppercase tracking-wide text-muted-foreground">
              {candidate.place_type}
            </div>
          )}
          {hasPlaceData ? (
            <div className="flex flex-wrap gap-x-4 gap-y-0.5 text-xs text-muted-foreground">
              {candidate.address && (
                <span className="inline-flex items-center gap-1">
                  <MapPin className="h-3 w-3" /> {candidate.address}
                </span>
              )}
              {candidate.phone && (
                <span className="inline-flex items-center gap-1">
                  <Phone className="h-3 w-3" /> {candidate.phone}
                </span>
              )}
            </div>
          ) : (
            candidate.snippet && (
              <p className="text-sm text-muted-foreground line-clamp-2">{candidate.snippet}</p>
            )
          )}
        </div>
        <Badge variant="muted" className="shrink-0 gap-1">
          <ExternalLink className="h-3 w-3" /> {candidate.source}
        </Badge>
      </div>
    </button>
  );
}

function SearchStatus({
  companyLen,
  searching,
  hasSearched,
  candidatesCount,
  error,
}: {
  companyLen: number;
  searching: boolean;
  hasSearched: boolean;
  candidatesCount: number;
  error: string | null;
}) {
  if (error) return <ErrorBanner message={error} />;
  if (companyLen < 2) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Search className="h-4 w-4" /> Tapez au moins 2 caractères pour lancer la recherche…
      </div>
    );
  }
  if (searching) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" /> Recherche sur Google…
      </div>
    );
  }
  if (hasSearched && candidatesCount === 0) {
    return (
      <div className="rounded-xl border border-border bg-muted/30 p-4 text-sm text-muted-foreground">
        Aucune entreprise trouvée. Vérifiez l'orthographe ou ajoutez une ville.
      </div>
    );
  }
  return null;
}

interface LabeledInputProps {
  icon: React.ReactNode;
  label: string;
  placeholder: string;
  value: string;
  onChange: (v: string) => void;
  disabled?: boolean;
  autoFocus?: boolean;
}

function LabeledInput({ icon, label, placeholder, value, onChange, disabled, autoFocus }: LabeledInputProps) {
  return (
    <label className="block">
      <span className="mb-1.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        {icon} {label}
      </span>
      <Input
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        autoFocus={autoFocus}
      />
    </label>
  );
}

function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/5 p-4 text-sm text-destructive">
      <div className="font-medium">Un problème est survenu</div>
      <div className="mt-1 text-destructive/80">{message}</div>
    </div>
  );
}
