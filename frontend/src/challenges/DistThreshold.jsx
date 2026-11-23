import {useEffect, useState} from "react";
import "./DistThreshold.css";

export default function DistThreshold({challenge, node, onDone, onNotRegistered}){
    const [view, setView] = useState(challenge);
    const [feedback, setFeedback] = useState(" ");


    useEffect(() => {
        let canceled = false;

        async function poll(){
            const res = await fetch(`/api/challenge/${node}/start`, {method: "POST"});
            if (res.status === 401) return onNotRegistered?.();
            const data = await res.json();
            if (canceled || data.error) return;
            setView(data);
            if (data.done) onDone?.();
        }

        poll();
        const id = setInterval(poll, 500);
        return () => {
            canceled = true;
            clearInterval(id);
        };
    

    }, [node, onDone, onNotRegistered]);


    async function handlePress(){
        setFeedback(" ")
        const res = await fetch(`/api/challenge/${node}/submit`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({}),
        });
        if (res.status ===401) return onNotRegistered?.();
        const data = await res.json();

        if (data.error === "locked") return setFeedback("Falied! Wait penalty out.");
        if (data.error === "not_reached") return setFeedback("Not there yet!");
        if (data.error) return setFeedback("Error. Status unknown.");

        if (data.done){
            setView(data);
            onDone?.();
            return;
        } 
        setView(data);

    }

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
                            {view.instruction} Target: {view.direction === "over" ? "above" : "below"} {view.threshold} dBm. Hurry up!
                        </p>
                        <p>{view.signal === "ok" ? `Signal: ${view.rssi} dBm` : "No signal"}</p>
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