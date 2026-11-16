import { useEffect, useState } from "react";
import "./Challenges.css";

export default function Challenges({ onDone, onNotRegistered }) {
    const [node, setNode] = useState(null); //the node player is on
    const [challenge, setChallenge] = useState(null); //whatever start() returned
    const [answer, setAnswer] = useState(""); //controlled input by the user
    const [feedback, setFeedback] = useState(""); //player feedback based on answers

    useEffect(() => {
        async function load() {
            const s = await fetch("/api/state"); //get which node player is on
            if (s.status === 401) return onNotRegistered?.(); 
            const state = await s.json();
            if (state.node === null) return onDone?.(); //if team finished all nodes, no challege to display
            setNode(state.node);

            const res = await fetch(`/api/challenge/${state.node}/start`, { method: "POST" }); 
            if (res.status === 401) return onNotRegistered?.();
            if (!res.ok) return onDone?.();
            setChallenge(await res.json());
        }
        load();
    }, [onDone, onNotRegistered]);

    async function handleSubmit(event) {
        event.preventDefault();
        setFeedback("");
        const res = await fetch(`/api/challenge/${node}/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer }),
        });
        if (res.status === 401) return onNotRegistered?.();
        const data = await res.json();
        if (data.correct) onDone?.();
        else setFeedback("wrong answer");
        setAnswer("");
    }

    if (!challenge) return <p>Loading challenge...</p>;

    return (
        <div className="challenge">
        <form className="challenge-card" onSubmit={handleSubmit}>
            <h2 className="challenge-question">{challenge.question}</h2>
            <input
                className="challenge-input"
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Your answer"
            />
            <button className="challenge-button" type="submit">Submit</button>
            {feedback && <p className="challenge-feedback">{feedback}</p>}
        </form>
        </div>
    );
}