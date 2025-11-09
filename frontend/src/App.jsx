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
          EchoType analyzes your posts and predicts your MBTI-inspired personality
          profile using natural language understanding.
        </p>
        <button className="intro-button" onClick={onStart}>
          Get Started
        </button>
      </div>
    </div>
  );
}

function MainScreen() {
  const [posts, setPosts] = useState([""]);

  const updatePost = (index, value) => {
    const next = [...posts];
    next[index] = value;
    setPosts(next);
  };

  const addPost = () => {
    setPosts([...posts, ""]);
  };

  const handleAnalyze = () => {
    const texts = posts.map(p => p.trim()).filter(p => p.length > 0);
    if (texts.length === 0) {
      alert("Please write at least one post.");
      return;
    }

    // later: call your backend here
    // fetch("/predict", { method: "POST", body: JSON.stringify({ texts }) })
    console.log("Would send to backend:", texts);
    alert("Check console: this is where /predict will be called.");
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
            Add one or more posts. More context helps the model understand your style.
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
                  placeholder="Type a post, thought, rant, or story..."
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
            <button className="analyze-button" onClick={handleAnalyze}>
              Analyze Personality
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

export default function App() {
  const [started, setStarted] = useState(false);
  return started ? (
    <MainScreen />
  ) : (
    <IntroScreen onStart={() => setStarted(true)} />
  );
}
