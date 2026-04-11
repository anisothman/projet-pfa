import { useState, useEffect } from "react";

export default function ResultDisplay() {
  const [entreprises, setEntreprises] = useState([]);
  const [entreprise, setEntreprise] = useState("");
  const [resultat, setResultat] = useState(null);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState(null);

  useEffect(() => {
    fetch("http://localhost:5000/api/companies")
      .then((res) => res.json())
      .then((data) => { if (data.success) setEntreprises(data.companies); })
      .catch(() => {});
  }, []);

  const analyserEntreprise = async () => {
    setLoading(true);
    setErreur(null);
    setResultat(null);
    try {
      const res = await fetch("http://localhost:5000/api/analyze", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ company_name: entreprise }),
      });
      const data = await res.json();
      if (!data.success) throw new Error(data.error);
      setResultat(data);
    } catch (err) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  const telechargerPDF = async () => {
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
    } catch (err) {
      setErreur("Erreur téléchargement PDF");
    }
  };

  return (
    <div style={{ maxWidth: 700, margin: "0 auto", padding: "2rem" }}>
      <h1>Analyse E-réputation</h1>

      {entreprises.length > 0 && (
        <p style={{ fontSize: 13, color: "gray" }}>
          Disponibles : {entreprises.join(", ")}
        </p>
      )}

      <input
        type="text"
        placeholder="Nom de l'entreprise (ex: apple)"
        value={entreprise}
        onChange={(e) => setEntreprise(e.target.value)}
        style={{ width: "100%", padding: 8, marginBottom: 10 }}
      />
      <button onClick={analyserEntreprise} disabled={loading}>
        {loading ? "Analyse en cours..." : "Analyser"}
      </button>

      {erreur && <p style={{ color: "red" }}>{erreur}</p>}

      {resultat && (
        <div style={{ marginTop: "2rem" }}>
          <h2>{resultat.company_name.toUpperCase()}</h2>

          <div style={{ background: "#f0f0f0", padding: 12, borderRadius: 8, marginBottom: 16 }}>
            <strong>Score : {resultat.rating.score}/100</strong>
            <p>{resultat.rating.justification}</p>
          </div>

          <h3>Diagnostic</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{resultat.diagnostic}</pre>

          <h3>Plan d'action</h3>
          <pre style={{ whiteSpace: "pre-wrap" }}>{resultat.plan_action}</pre>

          <button onClick={telechargerPDF} style={{ marginTop: 16 }}>
            Télécharger le PDF
          </button>
        </div>
      )}
    </div>
  );
}