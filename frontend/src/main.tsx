import { useId, useState } from "react";
import ReactDOM from "react-dom/client";
import ResultDisplay from "./components/ResultDisplay";

const styles = `
  * { margin: 0; padding: 0; box-sizing: border-box; }
  :root {
    --blue: #3B5BDB; --blue-dark: #2F4AC2; --blue-light: #EEF2FF; --blue-mid: #4C6EF5;
    --purple: #7048E8; --text-dark: #111827; --text-gray: #6B7280; --bg: #F8F9FC;
    --white: #FFFFFF; --green: #22C55E; --border: #E5E7EB;
  }
  body { font-family: 'Sora', sans-serif; }
  .localis-root { font-family: 'Sora', sans-serif; background: var(--white); color: var(--text-dark); overflow-x: hidden; }
  .localis-root.dark { --blue: #7c9bff; --blue-dark: #6589ff; --blue-light: #1e293b; --blue-mid: #93acff; --purple: #a78bfa; --text-dark: #e5e7eb; --text-gray: #9ca3af; --bg: #0f172a; --white: #111827; --green: #34d399; --border: #334155; }
  .localis-root.dark .nav { background: rgba(17,24,39,0.95); }
  .localis-root.dark .analytics-card, .localis-root.dark .feature-card, .localis-root.dark .step-icon-badge, .localis-root.dark .stat-badge, .localis-root.dark .stat-badge2, .localis-root.dark .btn-hero-secondary { background: #1f2937; }
  .localis-root.dark .chart-area { background: #0b1220; }
  .localis-root.dark .btn-hero-secondary { color: var(--text-dark); border-color: var(--border); }
  .localis-root.dark .btn-moon, .localis-root.dark .card-title, .localis-root.dark .feature-name, .localis-root.dark .step-content h3 { color: var(--text-dark); }
  .localis-root.dark .icon-blue { background: #1e293b; } .localis-root.dark .icon-purple { background: #2e1065; } .localis-root.dark .icon-green { background: #064e3b; } .localis-root.dark .icon-orange { background: #7c2d12; }
  .localis-root.dark .how-section { background: #111827; }
  .nav { position: sticky; top: 0; z-index: 100; display: flex; align-items: center; justify-content: space-between; padding: 0 48px; height: 70px; background: rgba(255,255,255,0.95); backdrop-filter: blur(12px); border-bottom: 1px solid var(--border); }
  .nav-logo { display: flex; align-items: center; gap: 10px; cursor: pointer; }
  .nav-logo-icon { width: 38px; height: 38px; border-radius: 10px; background: linear-gradient(135deg, #7048E8, #3B5BDB); display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px rgba(59,91,219,0.3); }
  .nav-links { display: flex; align-items: center; gap: 36px; }
  .nav-link { font-size: 14px; font-weight: 500; color: var(--text-gray); cursor: pointer; transition: color 0.2s; border: none; background: none; font-family: 'Sora', sans-serif; }
  .nav-link:hover, .nav-link.active { color: var(--blue); }
  .nav-right { display: flex; align-items: center; gap: 20px; }
  .btn-moon { background: none; border: none; cursor: pointer; font-size: 18px; color: var(--text-dark); }
  .hero { background: var(--bg); min-height: calc(100vh - 70px); display: flex; align-items: center; position: relative; overflow: hidden; padding: 60px 80px; background-image: linear-gradient(rgba(59,91,219,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(59,91,219,0.04) 1px, transparent 1px); background-size: 40px 40px; }
  .hero-content { flex: 1; max-width: 520px; z-index: 2; }
  .hero-badge { display: inline-flex; align-items: center; gap: 8px; background: rgba(59,91,219,0.08); border: 1px solid rgba(59,91,219,0.2); color: var(--blue); padding: 8px 16px; border-radius: 100px; font-size: 13px; font-weight: 500; margin-bottom: 28px; }
  .hero h1 { font-size: 64px; font-weight: 800; line-height: 1.05; color: var(--text-dark); margin-bottom: 16px; letter-spacing: -1.5px; }
  .hero h2 { font-size: 26px; font-weight: 500; color: var(--text-dark); margin-bottom: 20px; }
  .hero p { font-size: 15px; color: var(--text-gray); line-height: 1.7; margin-bottom: 36px; font-family: 'Inter', sans-serif; }
  .hero-btns { display: flex; gap: 14px; align-items: center; margin-bottom: 24px; }
  .btn-hero-primary { background: var(--blue); color: white; border: none; padding: 14px 28px; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 8px; font-family: 'Sora', sans-serif; box-shadow: 0 4px 16px rgba(59,91,219,0.35); }
  .btn-hero-primary:hover { background: var(--blue-dark); transform: translateY(-2px); }
  .btn-hero-secondary { background: white; color: var(--text-dark); border: 1.5px solid var(--border); padding: 14px 28px; border-radius: 12px; font-size: 15px; font-weight: 600; cursor: pointer; transition: all 0.2s; font-family: 'Sora', sans-serif; }
  .btn-hero-secondary:hover { border-color: var(--blue); color: var(--blue); }
  .hero-trust { display: flex; align-items: center; gap: 20px; }
  .trust-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: var(--text-gray); font-family: 'Inter', sans-serif; }
  .dot-green { width: 8px; height: 8px; border-radius: 50%; background: var(--green); }
  .hero-visual { flex: 1; display: flex; justify-content: flex-end; z-index: 2; }
  .analytics-card { background: white; border-radius: 24px; padding: 28px; width: 440px; box-shadow: 0 20px 60px rgba(59,91,219,0.12), 0 4px 16px rgba(0,0,0,0.06); position: relative; }
  .card-header { display: flex; align-items: center; gap: 12px; margin-bottom: 24px; }
  .card-icon { width: 36px; height: 36px; border-radius: 10px; background: linear-gradient(135deg, #7048E8, #3B5BDB); display: flex; align-items: center; justify-content: center; }
  .card-title { font-size: 16px; font-weight: 600; }
  .chart-area { background: var(--bg); border-radius: 16px; padding: 20px; height: 200px; position: relative; overflow: hidden; margin-bottom: 16px; }
  .bars { display: flex; align-items: flex-end; gap: 10px; height: 100%; padding-top: 20px; }
  .bar { flex: 1; border-radius: 6px 6px 0 0; background: linear-gradient(180deg, #93ACFF, #3B5BDB); opacity: 0.7; animation: barGrow 1s ease both; }
  @keyframes barGrow { from { transform: scaleY(0); transform-origin: bottom; } to { transform: scaleY(1); transform-origin: bottom; } }
  .line-svg { position: absolute; top: 0; left: 0; width: 100%; height: 100%; }
  .stat-badge { position: absolute; right: 28px; top: 32px; background: white; border-radius: 14px; padding: 12px 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 2px; }
  .stat-label { font-size: 10px; color: var(--text-gray); font-family: 'Inter', sans-serif; }
  .stat-value { font-size: 22px; font-weight: 700; color: var(--green); }
  .stat-badge2 { position: absolute; right: 28px; top: 130px; background: white; border-radius: 14px; padding: 12px 18px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); display: flex; flex-direction: column; gap: 2px; }
  .stat-value2 { font-size: 22px; font-weight: 700; color: var(--blue); }
  .section { padding: 100px 80px; }
  .section-title { font-size: 48px; font-weight: 800; text-align: center; color: var(--text-dark); margin-bottom: 16px; letter-spacing: -1px; line-height: 1.1; }
  .section-sub { text-align: center; font-size: 16px; color: var(--text-gray); font-family: 'Inter', sans-serif; margin-bottom: 72px; }
  .features-section { background: var(--bg); }
  .features-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; }
  .feature-card { background: white; border-radius: 20px; padding: 32px 24px; border: 1.5px solid var(--border); transition: transform 0.2s, box-shadow 0.2s; }
  .feature-card:hover { transform: translateY(-4px); box-shadow: 0 12px 40px rgba(59,91,219,0.1); }
  .feature-icon-wrap { width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center; margin-bottom: 20px; }
  .icon-blue { background: #EEF2FF; } .icon-purple { background: #F3F0FF; } .icon-green { background: #ECFDF5; } .icon-orange { background: #FFF7ED; }
  .feature-name { font-size: 17px; font-weight: 700; margin-bottom: 12px; }
  .feature-desc { font-size: 14px; color: var(--text-gray); line-height: 1.65; font-family: 'Inter', sans-serif; }
  .how-section { background: white; }
  .steps-list { max-width: 700px; margin: 0 auto; display: flex; flex-direction: column; gap: 64px; }
  .step-item { display: flex; align-items: flex-start; gap: 32px; }
  .step-num-wrap { position: relative; flex-shrink: 0; }
  .step-num { width: 64px; height: 64px; border-radius: 50%; background: var(--blue); display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 800; color: white; position: relative; z-index: 1; }
  .step-icon-badge { position: absolute; bottom: -6px; right: -6px; width: 28px; height: 28px; border-radius: 50%; background: white; border: 2px solid var(--blue); display: flex; align-items: center; justify-content: center; font-size: 12px; }
  .step-content h3 { font-size: 24px; font-weight: 700; margin-bottom: 10px; }
  .step-content p { font-size: 15px; color: var(--text-gray); line-height: 1.7; font-family: 'Inter', sans-serif; }
  .analysis-section { background: var(--bg); padding: 80px; }
  .cta-section { background: linear-gradient(135deg, #3B5BDB 0%, #2F4AC2 40%, #1E3A8A 100%); padding: 100px 80px; text-align: center; position: relative; overflow: hidden; }
  .cta-section::before { content: ''; position: absolute; inset: 0; background-image: linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px); background-size: 40px 40px; }
  .cta-title { font-size: 52px; font-weight: 800; color: white; margin-bottom: 20px; letter-spacing: -1px; position: relative; }
  .cta-sub { font-size: 17px; color: rgba(255,255,255,0.75); font-family: 'Inter', sans-serif; margin-bottom: 48px; max-width: 620px; margin-left: auto; margin-right: auto; line-height: 1.65; position: relative; }
  .cta-checks { display: flex; gap: 40px; justify-content: center; margin-bottom: 40px; position: relative; flex-wrap: wrap; }
  .cta-check { display: flex; align-items: center; gap: 10px; color: white; font-size: 15px; font-weight: 500; }
  .check-icon { width: 22px; height: 22px; border-radius: 50%; border: 2px solid var(--green); display: flex; align-items: center; justify-content: center; font-size: 11px; color: var(--green); }
  .btn-cta { background: white; color: var(--blue); border: none; padding: 16px 36px; border-radius: 14px; font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s; display: inline-flex; align-items: center; gap: 8px; font-family: 'Sora', sans-serif; position: relative; box-shadow: 0 4px 20px rgba(0,0,0,0.2); }
  .btn-cta:hover { transform: translateY(-2px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
  .cta-fine { color: rgba(255,255,255,0.55); font-size: 13px; margin-top: 20px; font-family: 'Inter', sans-serif; position: relative; }
  .footer-bar { background: linear-gradient(135deg, #3B5BDB 0%, #2F4AC2 100%); padding: 40px 80px; display: flex; align-items: center; justify-content: space-between; border-top: 1px solid rgba(255,255,255,0.15); gap: 24px; flex-wrap: wrap; }
  .footer-logo { display: flex; flex-direction: column; gap: 4px; }
  .footer-logo-row { display: flex; align-items: center; gap: 10px; }
  .footer-logo-name { font-size: 16px; font-weight: 700; color: white; }
  .footer-tagline { font-size: 13px; color: rgba(255,255,255,0.78); font-family: 'Inter', sans-serif; }
  .footer-links { display: flex; gap: 32px; }
  .footer-link { font-size: 14px; color: rgba(255,255,255,0.82); cursor: pointer; font-family: 'Inter', sans-serif; }
  .footer-link:hover { color: white; }
  .footer-copy { font-size: 13px; color: rgba(255,255,255,0.72); font-family: 'Inter', sans-serif; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
  .fade-up { animation: fadeUp 0.7s ease both; }
  .delay-1 { animation-delay: 0.1s; } .delay-2 { animation-delay: 0.2s; } .delay-3 { animation-delay: 0.3s; } .delay-4 { animation-delay: 0.4s; }
  @media (max-width: 1100px) {
    .hero { flex-direction: column; gap: 40px; padding: 40px 24px; }
    .hero h1 { font-size: 44px; }
    .analytics-card { width: min(100%, 560px); }
    .features-grid { grid-template-columns: repeat(2, 1fr); }
    .section, .analysis-section { padding: 72px 24px; }
    .footer-bar { padding: 28px 24px; }
    .nav { padding: 0 24px; }
  }
  @media (max-width: 700px) {
    .nav-links { display: none; }
    .hero-btns { flex-direction: column; align-items: stretch; }
    .features-grid { grid-template-columns: 1fr; }
    .section-title { font-size: 34px; }
    .cta-title { font-size: 36px; }
    .cta-section { padding: 72px 24px; }
  }
`;

type LogoIconProps = { size?: number };
const LogoIcon = ({ size = 40 }: LogoIconProps) => {
  const id = useId();
  const mainBlueGrad = `mainBlueGrad-${id}`;
  const lightBlueGrad = `lightBlueGrad-${id}`;
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id={mainBlueGrad} x1="0" y1="0" x2="100" y2="100"><stop stopColor="#5b7beb" /><stop offset="0.4" stopColor="#3b5bdb" /><stop offset="1" stopColor="#2b4bcb" /></linearGradient>
        <linearGradient id={lightBlueGrad} x1="0" y1="0" x2="100" y2="100"><stop stopColor="#ffffff" /><stop offset="1" stopColor="#e8edfc" /></linearGradient>
      </defs>
      <circle cx="50" cy="50" r="47" fill={`url(#${mainBlueGrad})`} stroke="#5b7beb" strokeWidth="2" />
      <path d="M50 28 C41 28 35 35.5 35 43.5 C35 52.5 50 68 50 68 C50 68 65 52.5 65 43.5 C65 35.5 59 28 50 28Z" fill={`url(#${lightBlueGrad})`} stroke="#3b5bdb" strokeWidth="1.8" />
      <rect x="41" y="38" width="18" height="14" rx="4" fill="#3b5bdb" />
      <circle cx="46" cy="44" r="2.5" fill="white" /><circle cx="54" cy="44" r="2.5" fill="white" />
      <circle cx="46.5" cy="44" r="1.2" fill="#5b7beb" /><circle cx="54.5" cy="44" r="1.2" fill="#5b7beb" />
      <rect x="47" y="48" width="6" height="1.5" rx="0.75" fill="white" opacity="0.8" />
      <line x1="47" y1="38" x2="45" y2="33" stroke="#3b5bdb" strokeWidth="1.8" strokeLinecap="round" />
      <line x1="53" y1="38" x2="55" y2="33" stroke="#3b5bdb" strokeWidth="1.8" strokeLinecap="round" />
      <circle cx="45" cy="32.5" r="2" fill="#5b7beb" /><circle cx="55" cy="32.5" r="2" fill="#5b7beb" />
      <path d="M50 22 L51.5 26.5 L56.5 27 L52.5 30.5 L53.5 35 L50 32.5 L46.5 35 L47.5 30.5 L43.5 27 L48.5 26.5 Z" fill="white" opacity="0.95" />
      <line x1="28" y1="28" x2="40" y2="40" stroke="#3b5bdb" strokeWidth="0.8" opacity="0.6" />
      <line x1="60" y1="60" x2="72" y2="72" stroke="#3b5bdb" strokeWidth="0.8" opacity="0.6" />
      <line x1="72" y1="28" x2="60" y2="40" stroke="#3b5bdb" strokeWidth="0.8" opacity="0.6" />
      <line x1="28" y1="72" x2="40" y2="60" stroke="#3b5bdb" strokeWidth="0.8" opacity="0.6" />
    </svg>
  );
};

const BrandLogo = ({ compact = false }: { compact?: boolean }) => (
  <div style={{ display: "flex", alignItems: "center" }}>
    <div style={{ width: compact ? 64 : 88, height: compact ? 64 : 88, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
      <LogoIcon size={compact ? 56 : 76} />
    </div>
  </div>
);

const DBIcon = () => (<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><ellipse cx="12" cy="6" rx="8" ry="3" fill="#3B5BDB"/><path d="M4 6v6c0 1.66 3.58 3 8 3s8-1.34 8-3V6" fill="#3B5BDB" fillOpacity="0.5"/><path d="M4 12v6c0 1.66 3.58 3 8 3s8-1.34 8-3v-6" fill="#3B5BDB" fillOpacity="0.3"/></svg>);
const BrainIcon = () => (<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M9 3C6.24 3 4 5.24 4 8c0 1.5.6 2.85 1.57 3.83C4.6 12.57 4 13.71 4 15c0 2.76 2.24 5 5 5h2v-4.5L9.5 14H8v-2h1.5L11 10.5V9h2v1.5L14.5 12H16v2h-1.5L13 15.5V20h2c2.76 0 5-2.24 5-5 0-1.29-.6-2.43-1.57-3.17C19.4 10.85 20 9.5 20 8c0-2.76-2.24-5-5-5-1.45 0-2.75.62-3.67 1.6C10.41 3.62 9.71 3 9 3z" fill="#7048E8"/></svg>);
const CheckListIcon = () => (<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="18" height="18" rx="4" fill="#22C55E" fillOpacity="0.2"/><path d="M7 12l3 3 7-7" stroke="#22C55E" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/><path d="M7 7h10M7 17h5" stroke="#22C55E" strokeWidth="1.5" strokeLinecap="round" opacity="0.5"/></svg>);
const DocIcon = () => (<svg width="24" height="24" viewBox="0 0 24 24" fill="none"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" fill="#F97316" fillOpacity="0.8"/><path d="M14 2v6h6" fill="#F97316" fillOpacity="0.4"/><path d="M8 13h8M8 17h5" stroke="white" strokeWidth="1.5" strokeLinecap="round"/></svg>);
const SearchIcon = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><circle cx="11" cy="11" r="8" stroke="white" strokeWidth="2.5"/><path d="M21 21l-4.35-4.35" stroke="white" strokeWidth="2.5" strokeLinecap="round"/></svg>);
const BoltIcon = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M13 2L4.5 13.5H11L10 22L20.5 10H14L13 2z" fill="white"/></svg>);
const StarIcon = () => (<svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" fill="white"/></svg>);

export default function LocalisAI() {
  const [activeSection, setActiveSection] = useState("home");
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [showAnalysis, setShowAnalysis] = useState(false);

  const scrollTo = (id: string) => {
    setActiveSection(id);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  const handleStartAnalysis = () => {
    setShowAnalysis(true);
    setTimeout(() => {
      document.getElementById("analysis")?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  };

  return (
    <div className={`localis-root ${isDarkMode ? "dark" : ""}`}>
      <style>{styles}</style>

      <nav className="nav">
        <div className="nav-logo" onClick={() => scrollTo("home")}><BrandLogo compact /></div>
        <div className="nav-links">
          <button className={`nav-link ${activeSection === "features" ? "active" : ""}`} onClick={() => scrollTo("features")}>Features</button>
          <button className={`nav-link ${activeSection === "how" ? "active" : ""}`} onClick={() => scrollTo("how")}>How it works</button>
          <button className="nav-link" onClick={handleStartAnalysis}>Analyse</button>
        </div>
        <div className="nav-right">
          <button className="btn-moon" onClick={() => setIsDarkMode((prev) => !prev)}>{isDarkMode ? "☀" : "☽"}</button>
        </div>
      </nav>

      <section id="home" className="hero">
        <div className="hero-content">
          <BrandLogo />
          <div className="hero-badge fade-up"><span>✦</span> AI-Powered Business Intelligence</div>
          <h1 className="fade-up delay-1">Localis AI</h1>
          <h2 className="fade-up delay-2">From Local Data to Smart Decisions</h2>
          <p className="fade-up delay-2">Harness the power of AI to analyze your local business using Google data. Get actionable insights, diagnostic reports, and strategic action plans in minutes.</p>
          <div className="hero-btns fade-up delay-3">
            <button className="btn-hero-primary" onClick={handleStartAnalysis}>Start Analysis →</button>
            <button className="btn-hero-secondary" onClick={() => scrollTo("how")}>See How It Works</button>
          </div>
          <div className="hero-trust fade-up delay-4">
            <div className="trust-item"><div className="dot-green"></div> No credit card required</div>
            <div className="trust-item"><div className="dot-green"></div> Quick results</div>
          </div>
        </div>
        <div className="hero-visual">
          <div className="analytics-card fade-up delay-2">
            <div className="card-header">
              <div className="card-icon"><LogoIcon size={18} /></div>
              <span className="card-title">Business Analytics</span>
              <span style={{marginLeft:"auto",color:"#3B5BDB",fontSize:20,cursor:"pointer"}}>+</span>
            </div>
            <div className="chart-area">
              <div className="bars">
                {[55, 65, 72, 80, 78, 90, 95].map((h, i) => (
                  <div key={i} className="bar" style={{ height: `${h}%`, animationDelay: `${i * 0.08}s` }} />
                ))}
              </div>
              <svg className="line-svg" viewBox="0 0 440 200" preserveAspectRatio="none">
                <polyline points="30,160 95,140 160,120 225,100 290,108 355,70 420,50" fill="none" stroke="#7048E8" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                {[30,95,160,225,290,355,420].map((x,i) => { const ys=[160,140,120,100,108,70,50]; return <circle key={i} cx={x} cy={ys[i]} r="5" fill="#7048E8" />; })}
              </svg>
            </div>
            <div className="stat-badge"><span className="stat-label">Rating Score</span><span className="stat-value">4.8/5</span></div>
            <div className="stat-badge2"><span className="stat-label">Insights</span><span className="stat-value2">127</span></div>
          </div>
        </div>
      </section>

      <section id="features" className="section features-section">
        <h2 className="section-title">Everything You Need for<br />Business Intelligence</h2>
        <p className="section-sub">Comprehensive tools powered by advanced AI to help your business thrive.</p>
        <div className="features-grid">
          {[
            { icon: <DBIcon />, bg: "icon-blue", name: "Google Data Extraction", desc: "Automatically collect and analyze comprehensive business data from Google Maps, Reviews, and search results." },
            { icon: <BrainIcon />, bg: "icon-purple", name: "AI Diagnostic Analysis", desc: "Powered by Gemini AI to identify strengths, weaknesses, and hidden opportunities." },
            { icon: <CheckListIcon />, bg: "icon-green", name: "Strategic Action Plans", desc: "Get prioritized short, medium, and long-term recommendations tailored to your needs." },
            { icon: <DocIcon />, bg: "icon-orange", name: "Professional PDF Reports", desc: "Download comprehensive, shareable reports with visualizations and actionable insights." },
          ].map((f, i) => (
            <div key={i} className="feature-card fade-up" style={{ animationDelay: `${i * 0.1}s` }}>
              <div className={`feature-icon-wrap ${f.bg}`}>{f.icon}</div>
              <div className="feature-name">{f.name}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </section>

      <section id="how" className="section how-section">
        <h2 className="section-title">How It Works</h2>
        <p className="section-sub">Get actionable insights in three simple steps</p>
        <div className="steps-list">
          {[
            { n: "01", icon: <SearchIcon />, title: "Enter Business Details", desc: "Simply provide your business name. We'll find all relevant data automatically." },
            { n: "02", icon: <BoltIcon />, title: "AI Analyzes Data", desc: "Our Gemini-powered AI processes thousands of data points to identify patterns and opportunities." },
            { n: "03", icon: <StarIcon />, title: "Get Your Report", desc: "Receive comprehensive insights, diagnostics, and a strategic action plan ready to implement." },
          ].map((s, i) => (
            <div key={i} className="step-item fade-up" style={{ animationDelay: `${i * 0.15}s` }}>
              <div className="step-num-wrap">
                <div className="step-num">{s.n}</div>
                <div className="step-icon-badge">{s.icon}</div>
              </div>
              <div className="step-content"><h3>{s.title}</h3><p>{s.desc}</p></div>
            </div>
          ))}
        </div>
      </section>

      {/* ===== TON COMPOSANT ResultDisplay ===== */}
      {showAnalysis && (
        <section id="analysis" className="analysis-section">
          <ResultDisplay />
        </section>
      )}

      <section id="pricing" className="cta-section">
        <h2 className="cta-title">Analyze Your Business Now</h2>
        <p className="cta-sub">Join hundreds of businesses making smarter decisions with AI-powered insights.</p>
        <div className="cta-checks">
          {["Instant AI-powered analysis", "Actionable recommendations", "Comprehensive PDF reports", "No credit card required"].map((c, i) => (
            <div key={i} className="cta-check"><div className="check-icon">✓</div>{c}</div>
          ))}
        </div>
        <button className="btn-cta" onClick={handleStartAnalysis}>Start Free Analysis →</button>
        <p className="cta-fine">Free to try • No installation required • Quick results</p>
      </section>

      <footer className="footer-bar">
        <div className="footer-logo">
          <div className="footer-logo-row">
            <div className="nav-logo-icon" style={{ width: 32, height: 32, borderRadius: 8 }}><LogoIcon size={16} /></div>
            <span className="footer-logo-name">Localis AI</span>
          </div>
          <span className="footer-tagline">From Local Data to Smart Decisions</span>
        </div>
        <div className="footer-links">
          <span className="footer-link">Privacy Policy</span>
          <span className="footer-link">Terms of Service</span>
          <span className="footer-link">Contact</span>
        </div>
        <span className="footer-copy">© 2026 Localis AI. All rights reserved.</span>
      </footer>
    </div>
  );
}

const root = document.getElementById("root");
if (root) {
  ReactDOM.createRoot(root).render(<LocalisAI />);
}
