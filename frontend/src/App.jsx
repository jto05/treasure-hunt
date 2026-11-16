import './App.css'
import { useEffect, useState} from "react";
import RegisterForm from "./RegisterForm";
import Distances from "./Distances";
import Challenges from "./Challenges";

/**
 * This file determines on the frontend, which screen should load for the player
 */

export default function App() {
  const [registered, setRegistered] = useState(null);
  const [phase, setPhase] = useState("travel"); //true when in challege, false if not

  useEffect(() => {
    async function check() {
      const res = await fetch("/api/state");
      if (res.ok) { //does team a cookie?
        const data = await res.json();
        setPhase(data.phase);
      }
      setRegistered(res.ok);
    }
    check();
  }, []);

  if (registered === null) return <p>Loading...</p>;

  //if registered is false, show RegisterForm
  if (!registered) {
    return <RegisterForm onSuccess={() => { setPhase("travel"); setRegistered(true); }} />;
  }

  //if registered and inChallenge, shows Challenges
  if (phase === "challenge") {
    return (
      <Challenges
        onDone={() => setPhase("travel")}
        onNotRegistered={() => setRegistered(false)}
      />
    );
  }

  //if registered and not inChallenge, shows Distances
  return (
    <Distances
      onStartChallenge={() => setPhase("challenge")}
      onNotRegistered={() => setRegistered(false)}
    />
  );
}