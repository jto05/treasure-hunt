//timebanktrivia.jsx
import { useEffect, useRef, useState } from "react";
import "./TimebankTrivia.css";

export default function TimebankTrivia({ challenge, node, onDone, onNotRegistered }) {
    const [view, setView] = useState(challenge); // latest start()/submit() response
    const [answer, setAnswer] = useState("");
    const [timeLeft, setTimeLeft] = useState(challenge.time_left_s ?? 0);
    const [busy, setBusy] = useState(false);
    // client-side anchor for the countdown display -- re-set every time the
    // server gives us a fresh authoritative time_left_s
    const deadlineRef = useRef(Date.now() + (challenge.time_left_s ?? 0) * 1000);

    async function submitAnswer(value) {
        if (busy) return;
        setBusy(true);
        const res = await fetch(`/api/challenge/${node}/submit`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer: value }),
        });
        setBusy(false);
        if (res.status === 401) return onNotRegistered?.();
        const data = await res.json();
        if (data.error) return; // transient/bad request -- leave the current view up
        setAnswer("");
        setView(data);
        if (data.done) onDone?.();
    }

    // reset the countdown anchor whenever a new authoritative view arrives
    useEffect(() => {
        if (view.status !== "active") return;
        deadlineRef.current = Date.now() + view.time_left_s * 1000;
        setTimeLeft(view.time_left_s);
    }, [view]);

    // ticking display; once it hits 0 force a submit so the server's lazy
    // expiry check can run (no answer to send -- see submit()'s contract)
    useEffect(() => {
        if (view.status !== "active") return;
        const id = setInterval(() => {
            const left = Math.max(0, (deadlineRef.current - Date.now()) / 1000);
            setTimeLeft(left);
            if (left <= 0) {
                clearInterval(id);
                submitAnswer(null);
            }
        }, 100);
        return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [view]);

    function handleTextSubmit(event) {
        event.preventDefault();
        submitAnswer(answer);
    }

    if (view.status === "failed") {
        return (
            <div className="challenge">
                <div className="challenge-card">
                    <h2 className="challenge-question">Time's up!</h2>
                    <p className="challenge-feedback">{view.message}</p>
                    <p className="timebank-progress">
                        {view.correct_count} / {view.required_correct} correct
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="challenge">
            <div className="challenge-card">
                <div className="timebank-bar">
                    <span className="timebank-time">{timeLeft.toFixed(1)}s</span>
                    <span className="timebank-progress">
                        {view.correct_count} / {view.required_correct}
                    </span>
                </div>

                <h2 className="challenge-question">{view.question}</h2>

                {view.choices ? (
                    <div className="timebank-choices">
                        {view.choices.map((choice) => (
                            <button
                                key={choice}
                                type="button"
                                className="timebank-choice"
                                disabled={busy}
                                onClick={() => submitAnswer(choice)}
                            >
                                {choice}
                            </button>
                        ))}
                    </div>
                ) : (
                    <form onSubmit={handleTextSubmit}>
                        <input
                            className="challenge-input"
                            value={answer}
                            onChange={(e) => setAnswer(e.target.value)}
                            placeholder="Your answer"
                            disabled={busy}
                        />
                        <button className="challenge-button" type="submit" disabled={busy}>
                            Submit
                        </button>
                    </form>
                )}

                {view.message && <p className="challenge-feedback">{view.message}</p>}
            </div>
        </div>
    );
}
