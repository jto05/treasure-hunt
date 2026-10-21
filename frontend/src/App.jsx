import './App.css'

import { useEffect, useState} from "react";
import RegisterForm from "./RegisterForm";
import Distances from "./Distances";

export default function App() {
  const [registered, setRegistered] = useState(null); // function to set registered

  useEffect(() => {
    fetch("/api/state").then((res) => setRegistered(res.ok)); //if response from fetch is true
  }, []);

  if (registered === null) return <p>Loading...</p>; // if component returns early

  return registered ? ( // determines which page to show next depending if registered or not
    <Distances onNotRegistered={() => setRegistered(false)} />
  ) : (
    <RegisterForm onSuccess={() => setRegistered(true)} />
  );
}