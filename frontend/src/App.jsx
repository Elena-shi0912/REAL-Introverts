import { useState } from "react";
import "./styles/App.css";
import "./index.css";
import IntroScreen from "./components/IntroScreen";
import MainScreen from "./components/MainScreen";
import ResultScreen from "./components/ResultScreen";

import { AnimatePresence, motion } from "framer-motion";

const swipeVariants = {
  initial: { y: "100%", opacity: 0 },
  animate: {
    y: 0,
    opacity: 1,
    transition: { duration: 0.7, ease: "easeInOut" },
  },
  exit: {
    y: "-100%",
    opacity: 0,
    transition: { duration: 0.7, ease: "easeInOut" },
  },
};

export default function App() {
  const [screen, setScreen] = useState("intro");
  const [result, setResult] = useState(null);

  return (
    <AnimatePresence mode="wait">
      {screen === "intro" && (
        <motion.div
          key="intro"
          variants={swipeVariants}
          initial=""
          animate="animate"
          exit="exit"
        >
          <IntroScreen onStart={() => setScreen("input")} />
        </motion.div>
      )}

      {screen === "input" && (
        <motion.div
          key="input"
          variants={swipeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <MainScreen
            onAnalyze={(realResult) => {
              setResult(realResult);
              setScreen("result");
            }}
          />
        </motion.div>
      )}

      {screen === "result" && result && (
        <motion.div
          key="result"
          variants={swipeVariants}
          initial="initial"
          animate="animate"
          exit="exit"
        >
          <ResultScreen
            result={result}
            onRestart={() => setScreen("input")}
          />
        </motion.div>
      )}
    </AnimatePresence>
  );
}