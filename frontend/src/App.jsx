import { useState } from "react";
import "./styles/App.css";
import "./index.css";
import IntroScreen from "./components/IntroScreen";
import MainScreen from "./components/MainScreen";
import ResultScreen from "./components/ResultScreen";

export default function App() {
  const [screen, setScreen] = useState("intro");
  const [result, setResult] = useState(null);

  if (screen === "intro") return <IntroScreen onStart={() => setScreen("input")} />;
  if (screen === "input")
    return (
      <MainScreen
        onAnalyze={(realResult) => {
          setResult(realResult);
          setScreen("result");
        }}
      />
    );
  if (screen === "result")
    return <ResultScreen result={result} onRestart={() => setScreen("input")} />;

  return null;
}