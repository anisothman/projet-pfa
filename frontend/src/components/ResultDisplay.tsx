import { useState, useEffect } from "react";

interface Rating {
  score: number;
  justification: string;
}

interface AnalysisResult {
  company_name: string;
  swot: string;          // ✅ corrigé
  action_plan: string;   // ✅ corrigé
  rating: Rating;
}

export default function ResultDisplay() {
  const [entreprises, setEntreprises] = useState<string[]>([]);
  const [entreprise, setEntreprise] = useState("");
  const [resultat, setResultat] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/companies")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setEntreprises(data.companies);
      })
      .catch(() => {});
  }, []);

  const analyserEntreprise = async () => {
    if (!entreprise.trim()) return;
    setLoading(true);
    setErreur(null);
    setResultat(null);

    try {
      const res = await fetch("http://localhost:5000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: entreprise.trim().toLowerCase(),
        }),
      });

      const data = await res.json();
      console.log("API RESULT =", data); // ✅ debug

      if (!data.success) throw new Error(data.error);
      setResultat(data);
    } catch (err: any) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  const telechargerPDF = async () => {
    if (!resultat) return;

    try {
      const res = await fetch("http://localhost:5000/api/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: resultat.company_name,
          diagnostic: resultat.swot,          // ✅ corrigé
          plan_action: resultat.action_plan,  // ✅ corrigé
          rating: resultat.rating,
        }),
      });

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `diagnostic_${resultat.company_name}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      setErreur("Erreur lors du téléchargement du PDF");
    }
  };

  const scoreColor = resultat
    ? resultat.rating.score >= 70
      ? "#22C55E"
      : resultat.rating.score >= 40
      ? "#F97316"
      : "#EF4444"
    : "#3B5BDB";

  return (
  <div style={{ maxWidth: 900, margin: "0 auto" }}>

    <h2 className="section-title">Analyse E-réputation</h2>
    <p className="section-sub">
      Entrez le nom d'une entreprise pour obtenir son diagnostic IA
    </p>

    {/* INPUT */}
    <div style={{ display: "flex", gap: 12, marginBottom: 40 }}>
      <input
        className="btn-hero-secondary"
        type="text"
        placeholder="ex: apple, samsung..."
        value={entreprise}
        onChange={(e) => setEntreprise(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && analyserEntreprise()}
        style={{ flex: 1 }}
      />

      <button className="btn-hero-primary" onClick={analyserEntreprise}>
        {loading ? "Analyse..." : "Analyser →"}
      </button>
    </div>

    {/* RESULT */}
    {resultat && (
      <div
        className="analytics-card"
        style={{
          width: "100%",
          padding: 40,
          borderRadius: 24,
        }}
      >

        {/* HEADER */}
        <div style={{ marginBottom: 30 }}>
          <h3 style={{ fontSize: 28, fontWeight: 800 }}>
            {resultat.company_name.toUpperCase()}
          </h3>

          <div style={{ marginTop: 10 }}>
            <span style={{ fontWeight: 600 }}>Score :</span>
            <span
              style={{
                marginLeft: 10,
                fontSize: 32,
                fontWeight: 800,
                color: "#22C55E",
              }}
            >
              {resultat.rating.score}/100
            </span>
          </div>
        </div>

        {/* GRID */}
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "1fr",
            gap: 24,
          }}
        >

          {/* SWOT */}
          <div className="feature-card">
            <h4 style={{ marginBottom: 12 }}>🔍 Diagnostic</h4>
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {resultat.swot}
            </pre>
          </div>

          {/* PLAN */}
          <div className="feature-card">
            <h4 style={{ marginBottom: 12 }}>🎯 Plan d'action</h4>
            <pre style={{ whiteSpace: "pre-wrap" }}>
              {resultat.action_plan}
            </pre>
          </div>

          {/* JUSTIFICATION */}
          <div className="feature-card">
            <h4 style={{ marginBottom: 12 }}>📊 Justification</h4>
            <p>{resultat.rating.justification}</p>
          </div>

        </div>

        {/* BUTTON */}
        <div style={{ marginTop: 30, textAlign: "center" }}>
          <button className="btn-cta" onClick={telechargerPDF}>
            📄 Télécharger PDF
          </button>
        </div>

      </div>
    )}
  </div>
);
}