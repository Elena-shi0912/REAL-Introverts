import { useState } from 'react';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';
import './index.css';

function IntroScreen({ onStart }) {
  return (
    <div className="intro-screen">
      <div className="intro-overlay" />
      <div className="intro-content">
        <h1 className="intro-title">Discover Your Personality Type</h1>
        <p className="intro-subtitle">Uncover how your words reflect who you are.</p>
        <p className="intro-description">
          MBTIx analyzes your posts and predicts your MBTI-inspired personality
          type using natural language patterns.
        </p>
        <button className="intro-button" onClick={onStart}>
          Get Started
        </button>
      </div>
    </div>
  );
}

function MainScreen({ onAnalyze }) {
  const [posts, setPosts] = useState([""]);
  const [error, setError] = useState("");

  const updatePost = (index, value) => {
    const next = [...posts];
    next[index] = value;
    setPosts(next);
  };

  const addPost = () => {
    setPosts([...posts, ""]);
  };

  const handleAnalyzeClick = () => {
    const texts = posts.map((p) => p.trim()).filter(Boolean);
    if (texts.length === 0) {
      setError("Write at least one post so we have something to analyze.");
      return;
    }
    setError("");

    // Fake result for now: static INTP result
    const fakeResult = {
      type: "INTP",
      label: "The Thinker",
      confidence: 0.86,
      traits: ["Introverted", "Intuitive", "Thinking", "Perceiving"],
      summary:
        "Analytical, curious, and independent. Often lives in ideas, enjoys complex problems, and prefers depth over small talk.",
    };

    onAnalyze(fakeResult);
  };

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-logo">MBTIx</div>
        <p className="app-tagline">Your MBTI — compiled from words.</p>
      </header>

      <main className="app-main">
        <section className="post-wrapper">
          <h2 className="post-title">Write like you do online.</h2>
          <p className="post-subtitle">
            Add one or more posts. More context helps MBTIx simulate a better prediction.
          </p>

          {posts.map((text, i) => (
            <div className="post-card" key={i}>
              <div className="post-header">
                <div className="avatar-circle">{i + 1}</div>
                <div className="post-user-info">
                  <div className="post-name">Your Post #{i + 1}</div>
                  <div className="post-handle">@you</div>
                </div>
              </div>

              <div className="post-body">
                <textarea
                  className="post-textarea"
                  placeholder="Type a post, thought, rant, or story as you normally would..."
                  value={text}
                  onChange={(e) => updatePost(i, e.target.value)}
                />
              </div>
            </div>
          ))}

          <div className="post-actions">
            <button className="add-post-button" onClick={addPost}>
              + Add another post
            </button>
            <button className="analyze-button" onClick={handleAnalyzeClick}>
              Analyze Personality
            </button>
          </div>

          {error && <p className="error-text">{error}</p>}
        </section>
      </main>
    </div>
  );
}

function ResultScreen({ result, onRestart }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-logo">MBTIx</div>
        <p className="app-tagline">Your MBTI — compiled from words.</p>
      </header>

      <main className="app-main result-layout">
        <section className="result-card">
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

          <div className="result-confidence">
            <div className="result-confidence-label">
              Model confidence (simulated)
            </div>
            <div className="result-bar-bg">
              <div
                className="result-bar-fill"
                style={{ width: `${result.confidence * 100}%` }}
              ></div>
            </div>
            <div className="result-confidence-value">
              {(result.confidence * 100).toFixed(1)}%
            </div>
          </div>

          <p className="result-note">
            This result is currently static (INTP) for demo purposes. In the full
            system, this screen will reflect live predictions from the deployed model.
          </p>

          <div className="result-actions">
            <button className="result-secondary" onClick={onRestart}>
              Try another sample
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default function App() {
  const [screen, setScreen] = useState("intro");
  const [result, setResult] = useState(null);

  if (screen === "intro") {
    return <IntroScreen onStart={() => setScreen("input")} />;
  }

  if (screen === "input") {
    return (
      <MainScreen
        onAnalyze={(fakeResult) => {
          setResult(fakeResult);
          setScreen("result");
        }}
      />
    );
  }

  if (screen === "result") {
    return (
      <ResultScreen
        result={result}
        onRestart={() => setScreen("input")}
      />
    );
  }

  return null;
}
