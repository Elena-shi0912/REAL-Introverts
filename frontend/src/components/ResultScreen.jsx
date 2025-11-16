import "../styles/ResultScreen.css";

export default function ResultScreen({ result, onRestart }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-logo">MBTIx</div>
        <p className="app-tagline">Your MBTI — compiled from words.</p>
      </header>

      <main className="app-main result-layout full-width">
        <section className="result-card result-flex">
          <div className="result-content">
            <div className="result-label">Predicted Type</div>
            <div className="result-type">
              {result.type}
              <span className="result-alias">{result.label}</span>
            </div>

            <div className="result-traits">
              {result.traits.map((t) => (
                <span key={t} className="result-pill">
                  {t}
                </span>
              ))}
            </div>

            <p className="result-summary">{result.summary}</p>

            <div className="result-actions">
              <button className="result-secondary" onClick={onRestart}>
                Try another sample
              </button>
            </div>
          </div>

          <img
            src={`/${result.type}.png`}
            alt={`${result.type} illustration`}
            className="result-image"
          />
        </section>
      </main>
    </div>
  );
}
