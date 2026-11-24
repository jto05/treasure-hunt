import {useEffect, useState} from "react";
import "./DistThreshold.css";

export default function DistThreshold({challenge, node, onDone, onNotRegistered}){
    const [view, setView] = useState(challenge);
    const [feedback, setFeedback] = useState(" ");

    
    useEffect(() => {
        let canceled = false; // Page is running true/false.

        // Attempt to start challenge. Run checks.
        async function poll(){
            const res = await fetch(`/api/challenge/${node}/start`, {method: "POST"});
            if (res.status === 401) return onNotRegistered?.();
            const data = await res.json();
            if (canceled || data.error) return;
            setView(data);
            if (data.done) onDone?.();
        }

        // Start challenge.
        poll();
        const id = setInterval(poll, 500); // Check ever 500 ms.
        // Reset when removed.
        return () => {
            canceled = true;
            clearInterval(id);
        };
    

    }, [node, onDone, onNotRegistered]);

    // When button is pressed, move to next round or end challenge.
    async function handlePress(){
        setFeedback(" ") // Clear feedback.
        // Call submit function.
        const res = await fetch(`/api/challenge/${node}/submit`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({}),
        });
        if (res.status ===401) return onNotRegistered?.();
        const data = await res.json(); // Server response.

        // Update team on current state.
        if (data.error === "locked") return setFeedback("Failed! Wait penalty out.");
        if (data.error === "not_reached") return setFeedback("Not there yet!");
        if (data.error) return setFeedback("Error. Status unknown.");

        // On completed challenge move on.
        if (data.done){
            setView(data);
            onDone?.();
            return;
        } 
        setView(data); // Next round.

    }

    // Page structure.
    return (
        <div className="challenge">
            <div className="challenge-card">
                <h2 className="challenge-question">
                    Round {view.round} of {view.rounds}
                </h2>
                {view.state === "penalty" ? (
                    <p>Too slow! Penalty wait time: {Math.ceil(view.penalty_remaining)}s</p>
                ) : (
                    <>
                        <p>
                            {view.instruction} Get a {view.direction === "over" ? "weaker" : "stronger"} signal of {view.threshold} dBm.
                        </p>
                        <p>{view.signal === "ok" ? `Current signal: ${view.rssi} dBm` : "No signal"}</p>
                        {view.state === "running" && (
                            <p className="challenge-timer">{Math.ceil(view.remaining)}s</p>
                        )}
                    </>
                )}

                {view.can_press && view.met &&(
                    <button className="challenge-button" onClick={handlePress}>
                        Made it!
                    </button>
                )}
                <p className="challenge-feedback">{feedback}</p>
            </div>
        </div>
    );
}