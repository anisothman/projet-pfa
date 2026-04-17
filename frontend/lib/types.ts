export type Impact = "critique" | "majeur" | "modéré" | "faible";
export type Priority = "P0" | "P1" | "P2" | "P3";

export interface Company {
  id_entreprise: string;
  nom: string;
  adresse: string;
  telephone: string | null;
  site_web: string | null;
  categorie: string | null;
  note_moyenne: number | null;
  nombre_avis: number | null;
}

export interface DiagnosticItem {
  titre: string;
  description: string;
  impact?: Impact | null;
}

export interface Diagnostic {
  points_forts: DiagnosticItem[];
  points_faibles: DiagnosticItem[];
  opportunites: DiagnosticItem[];
  menaces: DiagnosticItem[];
}

export interface Action {
  action: string;
  description: string;
  priorite?: Priority | null;
  delai_jours?: number | null;
  delai_mois?: number | null;
}

export interface KPI {
  metrique: string;
  baseline: string | number | null;
  cible: string | number | null;
  frequence_mesure: string | null;
}

export interface Risk {
  risque: string;
  probabilite: string | null;
  impact: Impact | null;
  mitigation: string | null;
}

export interface ActionPlan {
  resume_executif: string | null;
  court_terme: Action[];
  moyen_terme: Action[];
  long_terme: Action[];
  kpis?: KPI[] | null;
  risques?: Risk[] | null;
}

export interface Metadata {
  date_analyse: string;
  version_prompt: string;
  modele: string | null;
  provider: "openai" | "gemini" | null;
  temps_reponse_ms: number | null;
  langue: string;
  id_analyse: string;
}

export interface AnalysisReport {
  id: string;
  entreprise: Company;
  diagnostic: Diagnostic;
  plan_action: ActionPlan;
  metadonnees: Metadata;
}

export type ProgressStage =
  | "queued"
  | "serp_started" | "serp_done"
  | "diagnostic_started" | "diagnostic_done"
  | "plan_started" | "plan_done"
  | "pdf_ready"
  | "error";

export interface ProgressEvent {
  stage: ProgressStage;
  message: string;
  report_id: string | null;
  progress: number;
  detail?: Record<string, unknown> | null;
}

export interface Candidate {
  id: string;
  title: string;
  url: string;
  snippet: string;
  source: string;
  address?: string | null;
  rating?: number | null;
  reviews?: number | null;
  phone?: string | null;
  place_type?: string | null;
  thumbnail?: string | null;
}

export interface CandidatesResponse {
  query: string;
  candidates: Candidate[];
}
