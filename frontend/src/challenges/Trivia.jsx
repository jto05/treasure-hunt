//trivia.jsx
import { useState } from "react";
import "./Trivia.css";

export default function Trivia({challenge, node, onDone, onNotRegistered}) {
    const [answer, setAnswer] = useState("");
    const [feedback, setFeedback] = useState("");

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
        if (data.error) setFeedback("Something went wrong.");
        else if (data.done) onDone?.();
        else setFeedback("wrong answer");
        setAnswer("");
    }

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