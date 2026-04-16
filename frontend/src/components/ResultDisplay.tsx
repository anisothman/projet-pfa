import { useState, useEffect } from "react";

interface Rating {
  score: number;
  justification: string;
}

interface AnalysisResult {
  company_name: string;
  swot: string;
  action_plan: string;
  rating: Rating;
}

export default function ResultDisplay() {
  const [entreprises, setEntreprises] = useState<string[]>([]);
  const [entreprise, setEntreprise] = useState("");
  const [resultat, setResultat] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [erreur, setErreur] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:5000/api/companies")
      .then((res) => res.json())
      .then((data) => {
        if (data.success) setEntreprises(data.companies);
      })
      .catch(() => {});
  }, []);

  const removeStars = (text: string) => {
    if (!text) return "";
    return text.replace(/\*\*/g, "").replace(/\*/g, "");
  };

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
      console.log("API RESULT =", data);

      

      if (!data.success) throw new Error(data.error);

      const cleanedData = {
        ...data,
        swot: removeStars(data.swot),
        action_plan: removeStars(data.action_plan),
        rating: {
          ...data.rating,
          justification: removeStars(data.rating.justification),
        },
      };

      setResultat(cleanedData);
    } catch (err: any) {
      setErreur(err.message);
    } finally {
      setLoading(false);
    }
  };

  const telechargerPDF = async () => {
    if (!resultat) return;
    setPdfLoading(true);

    try {
      const res = await fetch("http://localhost:5000/api/generate-pdf", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          company_name: resultat.company_name,
          rating: resultat.rating,
          swot: resultat.swot,
          action_plan: resultat.action_plan,
        }),
      });

      if (!res.ok) throw new Error(`Erreur HTTP: ${res.status}`);

      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `diagnostic_${resultat.company_name}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      setErreur("Erreur lors du téléchargement du PDF: " + err.message);
    } finally {
      setPdfLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 70) return "#10B981";
    if (score >= 40) return "#F59E0B";
    return "#EF4444";
  };

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: "20px" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:opsz,wght@14..32,300;14..32,400;14..32,500;14..32,600;14..32,700;14..32,800&display=swap');
        * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }
        .main-title {
          font-size: 2.5rem; font-weight: 800;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text; margin-bottom: 0.75rem; letter-spacing: -0.02em;
        }
        .subtitle { font-size: 1.125rem; color: #6B7280; margin-bottom: 2rem; font-weight: 400; }
        .input-wrapper { display: flex; gap: 1rem; margin-bottom: 2.5rem; }
        .search-input {
          flex: 1; padding: 1rem 1.25rem; font-size: 1rem;
          border: 2px solid #E5E7EB; border-radius: 1rem;
          transition: all 0.3s ease; background: white; font-weight: 500;
        }
        .search-input:focus { outline: none; border-color: #6366F1; box-shadow: 0 0 0 3px rgba(99,102,241,0.1); }
        .search-input::placeholder { color: #9CA3AF; font-weight: 400; }
        .analyze-btn {
          padding: 1rem 2rem; font-size: 1rem; font-weight: 600;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
          color: white; border: none; border-radius: 1rem; cursor: pointer;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .analyze-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(99,102,241,0.4); }
        .analyze-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        .result-card {
          background: white; border-radius: 1.5rem; padding: 2.5rem;
          box-shadow: 0 20px 40px -12px rgba(0,0,0,0.1); animation: fadeIn 0.5s ease-out;
        }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .company-name {
          font-size: 2rem; font-weight: 800;
          background: linear-gradient(135deg, #1F2937 0%, #4B5563 100%);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent;
          background-clip: text; margin-bottom: 1rem; letter-spacing: -0.02em;
        }
        .rating-container {
          display: flex; align-items: center; gap: 0.75rem;
          margin-bottom: 2rem; padding-bottom: 1.5rem; border-bottom: 2px solid #F3F4F6;
        }
        .rating-label { font-size: 0.875rem; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.05em; }
        .rating-value { font-size: 1.5rem; font-weight: 700; line-height: 1; }
        .feature-grid { display: grid; gap: 1.5rem; margin-bottom: 2rem; }
        .feature-item {
          background: #F9FAFB; border-radius: 1rem; padding: 1.5rem;
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .feature-item:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
        .diagnostic-title { font-size: 1.125rem; font-weight: 700; margin-bottom: 0.75rem; color: #6366F1; }
        .action-title { font-size: 1.125rem; font-weight: 700; margin-bottom: 0.75rem; color: #8B5CF6; }
        .justification-title { font-size: 1.125rem; font-weight: 700; margin-bottom: 0.75rem; color: #EC4899; }
        .feature-content { font-size: 0.9375rem; line-height: 1.6; color: #4B5563; white-space: pre-wrap; font-weight: 400; }
        .pdf-btn {
          width: 100%; padding: 1rem; font-size: 1rem; font-weight: 600;
          background: linear-gradient(135deg, #6366F1 0%, #8B5CF6 100%);
          color: white; border: none; border-radius: 1rem; cursor: pointer; transition: all 0.3s ease;
        }
        .pdf-btn:hover:not(:disabled) { transform: translateY(-2px); box-shadow: 0 10px 25px -5px rgba(99,102,241,0.4); }
        .pdf-btn:disabled { opacity: 0.7; cursor: not-allowed; }
        .error-message {
          background: #FEE2E2; border-left: 4px solid #EF4444; padding: 1rem;
          border-radius: 0.5rem; margin-bottom: 1rem; color: #991B1B; font-weight: 500; font-size: 0.875rem;
        }
        @media (max-width: 768px) {
          .result-card { padding: 1.5rem; }
          .company-name { font-size: 1.5rem; }
          .rating-value { font-size: 1.25rem; }
          .main-title { font-size: 1.75rem; }
          .input-wrapper { flex-direction: column; }
        }
      `}</style>

      <h2 className="main-title">Analyse E-réputation</h2>
      <p className="subtitle">
        Entrez le nom d'une entreprise pour obtenir son diagnostic IA
      </p>

      <div className="input-wrapper">
        <input
          className="search-input"
          type="text"
          placeholder="ex: Apple, Samsung, Google"
          value={entreprise}
          onChange={(e) => setEntreprise(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && analyserEntreprise()}
        />
        <button
          className="analyze-btn"
          onClick={analyserEntreprise}
          disabled={loading}
        >
          {loading ? "Analyse en cours..." : "Analyser"}
        </button>
      </div>

      {erreur && <div className="error-message">{erreur}</div>}

      {resultat && (
        <div className="result-card">
          <h3 className="company-name">
            {resultat.company_name.toUpperCase()}
          </h3>

          <div className="rating-container">
            <span className="rating-label">Score de réputation</span>
            <span
              className="rating-value"
              style={{ color: getScoreColor(resultat.rating.score) }}
            >
              {resultat.rating.score}/100
            </span>
          </div>

          <div className="feature-grid">
            <div className="feature-item">
              <div className="diagnostic-title">Diagnostic stratégique</div>
              <div className="feature-content">{resultat.swot}</div>
            </div>

            <div className="feature-item">
              <div className="action-title">Plan d'action recommandé</div>
              <div className="feature-content">{resultat.action_plan}</div>
            </div>

            <div className="feature-item">
              <div className="justification-title">Justification du score</div>
              <div className="feature-content">
                {resultat.rating.justification}
              </div>
            </div>
          </div>

          <button
            className="pdf-btn"
            onClick={telechargerPDF}
            disabled={pdfLoading}
          >
            {pdfLoading ? "📄 Génération du PDF..." : "📥 Télécharger le rapport PDF"}
          </button>
        </div>
      )}
    </div>
  );
}
