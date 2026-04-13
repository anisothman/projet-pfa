import { useState, useEffect } from "react";

interface Rating {
  score: number;
  justification: string;
}

interface AnalysisResult {
  company_name: string;
  diagnostic: string;
  plan_action: string;
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
        body: JSON.stringify({ company_name: entreprise.trim().toLowerCase() }),
      });
      const data = await res.json();
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
          diagnostic: resultat.diagnostic,
          plan_action: resultat.plan_action,
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
    <div style={{ maxWidth: 800, margin: "0 auto", fontFamily: "'Sora', sans-serif" }}>

      {/* Titre */}
      <h2 style={{ fontSize: 32, fontWeight: 800, color: "#111827", marginBottom: 8 }}>
        Analyse E-réputation
      </h2>
      <p style={{ color: "#6B7280", marginBottom: 32, fontFamily: "'Inter', sans-serif" }}>
        Entrez le nom d'une entreprise pour obtenir son diagnostic IA
      </p>

      {/* Entreprises disponibles */}
      {entreprises.length > 0 && (
        <div style={{ marginBottom: 20, padding: "10px 16px", background: "#EEF2FF", borderRadius: 10 }}>
          <span style={{ fontSize: 13, color: "#3B5BDB", fontWeight: 500 }}>
            Disponibles : {entreprises.join(", ")}
          </span>
        </div>
      )}

      {/* Input + Bouton */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <input
          type="text"
          placeholder="ex: apple, samsung..."
          value={entreprise}
          onChange={(e) => setEntreprise(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyserEntreprise()}
          style={{
            flex: 1, padding: "14px 18px", borderRadius: 12,
            border: "1.5px solid #E5E7EB", fontSize: 15,
            fontFamily: "'Sora', sans-serif", outline: "none",
          }}
        />
        <button
          onClick={analyserEntreprise}
          disabled={loading}
          style={{
            background: loading ? "#93ACFF" : "#3B5BDB",
            color: "white", border: "none",
            padding: "14px 28px", borderRadius: 12,
            fontSize: 15, fontWeight: 600, cursor: loading ? "not-allowed" : "pointer",
            fontFamily: "'Sora', sans-serif", transition: "background 0.2s",
          }}
        >
          {loading ? "Analyse..." : "Analyser →"}
        </button>
      </div>

      {/* Erreur */}
      {erreur && (
        <div style={{ background: "#FEE2E2", border: "1px solid #FCA5A5", borderRadius: 10, padding: "12px 16px", marginBottom: 24, color: "#DC2626", fontSize: 14 }}>
          {erreur}
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div style={{ textAlign: "center", padding: "40px 0", color: "#6B7280" }}>
          <div style={{ fontSize: 32, marginBottom: 12 }}>⏳</div>
          <p>Analyse en cours avec Gemini AI...</p>
        </div>
      )}

      {/* Résultat */}
      {resultat && (
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>

          {/* Header entreprise + score */}
          <div style={{ background: "white", borderRadius: 20, border: "1.5px solid #E5E7EB", padding: "24px 28px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <p style={{ fontSize: 13, color: "#6B7280", marginBottom: 4 }}>Entreprise analysée</p>
              <h3 style={{ fontSize: 28, fontWeight: 800, color: "#111827", textTransform: "uppercase" }}>
                {resultat.company_name}
              </h3>
            </div>
            <div style={{ textAlign: "center" }}>
              <div style={{ fontSize: 48, fontWeight: 800, color: scoreColor, lineHeight: 1 }}>
                {resultat.rating.score}
              </div>
              <div style={{ fontSize: 13, color: "#6B7280" }}>/100</div>
            </div>
          </div>

          {/* Justification score */}
          <div style={{ background: "#F8F9FC", borderRadius: 14, padding: "16px 20px", borderLeft: `4px solid ${scoreColor}` }}>
            <p style={{ fontSize: 13, color: "#6B7280", marginBottom: 4, fontWeight: 600 }}>Justification du score</p>
            <p style={{ fontSize: 14, color: "#374151", fontFamily: "'Inter', sans-serif", lineHeight: 1.6 }}>
              {resultat.rating.justification}
            </p>
          </div>

          {/* Diagnostic */}
          <div style={{ background: "white", borderRadius: 20, border: "1.5px solid #E5E7EB", padding: "24px 28px" }}>
            <h4 style={{ fontSize: 18, fontWeight: 700, color: "#111827", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              🔍 Diagnostic
            </h4>
            <pre style={{ whiteSpace: "pre-wrap", fontFamily: "'Inter', sans-serif", fontSize: 14, color: "#374151", lineHeight: 1.7, margin: 0 }}>
              {resultat.diagnostic}
            </pre>
          </div>

          {/* Plan d'action */}
          <div style={{ background: "white", borderRadius: 20, border: "1.5px solid #E5E7EB", padding: "24px 28px" }}>
            <h4 style={{ fontSize: 18, fontWeight: 700, color: "#111827", marginBottom: 16, display: "flex", alignItems: "center", gap: 8 }}>
              🎯 Plan d'action
            </h4>
            <pre style={{ whiteSpace: "pre-wrap", fontFamily: "'Inter', sans-serif", fontSize: 14, color: "#374151", lineHeight: 1.7, margin: 0 }}>
              {resultat.plan_action}
            </pre>
          </div>

          {/* Bouton PDF */}
          <button
            onClick={telechargerPDF}
            style={{
              background: "linear-gradient(135deg, #7048E8, #3B5BDB)",
              color: "white", border: "none",
              padding: "16px 32px", borderRadius: 14,
              fontSize: 16, fontWeight: 600, cursor: "pointer",
              fontFamily: "'Sora', sans-serif",
              boxShadow: "0 4px 16px rgba(59,91,219,0.35)",
            }}
          >
            📄 Télécharger le rapport PDF
          </button>
        </div>
      )}
    </div>
  );
}