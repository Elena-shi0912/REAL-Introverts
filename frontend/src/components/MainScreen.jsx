import { useState } from "react";
import { MBTI_INFO } from "../assets/mbtiInfo";
import "../styles/MainScreen.css";
import { motion, AnimatePresence } from "framer-motion";

export default function MainScreen({ onAnalyze }) {
  const [posts, setPosts] = useState([""]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const updatePost = (index, value) => {
    const next = [...posts];
    next[index] = value;
    setPosts(next);
  };

  const addPost = () => {
    setPosts((prev) => [...prev, ""]);
    setTimeout(() => {
      const last = document.querySelector(".post-card:last-child");
      if (last) {
        last.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 100);
  };

  const removePost = (index) => {
    // If it's the only post, reset to one empty box instead of deleting everything
    if (posts.length === 1) {
      setPosts([""]);
      return;
    }

    setPosts(posts.filter((_, i) => i !== index));
  };

  const handleAnalyzeClick = async () => {
    const texts = posts.map((p) => p.trim()).filter(Boolean);

    if (texts.length === 0) {
      setError("Write at least one post so we have something to analyze.");
      return;
    }

    setError("");
    setLoading(true);

    try {
      const response = await fetch(
        "https://mbtibackend-341002537347.us-central1.run.app/predict",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text: texts.join(" ") }),
        }
      );

      if (!response.ok) throw new Error(`Server error: ${response.status}`);

      const data = await response.json();
      const type = data.prediction || "Unknown";
      const info = MBTI_INFO[type] || {
        label: "Unknown Type",
        traits: [],
        summary: "No information available for this type.",
      };

      onAnalyze({
        type,
        label: info.label,
        traits: info.traits,
        summary: info.summary,
      });
    } catch (err) {
      console.error("Error calling backend:", err);
      setError("Could not connect to backend. Please try again later.");
    } finally {
      setLoading(false);
    }
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

          <AnimatePresence>
            {posts.map((text, i) => (
              <motion.div
                key={i}
                className="post-card"
                initial={{ opacity: 0, y: 40 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -30 }}
                transition={{ duration: 0.25, ease: "easeInOut" }}
                layout
              >
                <div className="post-header">
                  <div className="avatar-circle">{i + 1}</div>
                  <div className="post-user-info">
                    <div className="post-name">Your Post #{i + 1}</div>
                    <div className="post-handle">@you</div>
                  </div>

                  {/* 🗑 Remove button */}
                  <button
                    className="remove-post-button"
                    onClick={() => removePost(i)}
                    disabled={posts.length === 1}
                    title={
                      posts.length === 1
                        ? "At least one post is required"
                        : "Remove this post"
                    }
                  >
                    ✕
                  </button>
                </div>

                <div className="post-body">
                  <textarea
                    className="post-textarea"
                    placeholder="Type a post, thought, rant, or story as you normally would..."
                    value={text}
                    onChange={(e) => updatePost(i, e.target.value)}
                  />
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          <div className="post-actions">
            <button className="add-post-button" onClick={addPost}>
              + Add another post
            </button>
            <button
              className="analyze-button"
              onClick={handleAnalyzeClick}
              disabled={loading}
            >
              {loading ? "Analyzing..." : "Analyze Personality"}
            </button>
          </div>

          {error && <p className="error-text">{error}</p>}
        </section>
      </main>
    </div>
  );
}
