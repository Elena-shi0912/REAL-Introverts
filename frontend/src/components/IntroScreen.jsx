import "../styles/IntroScreen.css";

export default function IntroScreen({ onStart }) {
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
