import { useEffect, useState} from "react";
import "./MemoryMatrix.css";

export default function MemoryMatrix({challenge, node, onDone, onNotRegistered}){
    const [view, setView] = useState(challenge);
    const [phase, setPhase] = useState("showing"); //three phases: showing, input, checking
    const [lit, setLit] = useState(null); //color glowing
    const [taps, setTaps] = useState([]); //user input
    const [feedback, setFeedback] = useState(" ");
    const START_DELAY = 1500; 

    //user effect plays the sequence
    useEffect(() => {
        //reset the phase and any player input
        setPhase("showing");
        setTaps([]);
        setLit(null);

        //flash time and short wait
        //goes through each color in the squence and flashes the appropriate color
        const step = view.show_ms + 500; 
        const timers = [];
        view.sequence.forEach((color, i) => {
            timers.push(setTimeout(() => setLit(color), 500 + i * step));
            timers.push(setTimeout(() => setLit(null), 500 + i * step + view.show_ms));
        });
        
        //once sequence plays, we switch to input mode
        timers.push(setTimeout(() => {
            setPhase("input");
            setFeedback(" ");
         }, START_DELAY + view.sequence.length * step));

        return () => timers.forEach(clearTimeout);
    }, [view]);

    //handles the user input
    async function handleTap(color){
        if(phase !== "input") return; //does take user input if not in input mode
        const next = [...taps, color];
        setTaps(next);
        if (next.length < view.sequence.length) return;

        setPhase("checking");
        //submits input response to check with server
        const res = await fetch(`/api/challenge/${node}/submit`, {
            method: "POST",
            headers: {"Content-Type":"application/json"},
            body: JSON.stringify({ answer: next}),
        });

        if (res.status === 401) return onNotRegistered?.();
        const data = await res.json();

        if(data.error){
            setFeedback("Something went wrong");
            setTaps([]);
            setPhase("input");
            return;
        }

        if(data.done) return onDone?.();

        setFeedback(data.correct ? "Correct!" : "Wrong. Try again.");
        setView(data); //triggers new sequence
    }

    return(
        <div className="challenge">
            <div className="challenge-card">
                <h2 className="challenge-question">
                    Round {view.round} of {view.rounds}
                </h2>
                <p>
                    {phase === "showing" && "Watch: "}
                    {phase === "input" && `Your turn (${taps.length}/${view.sequence.length})`}
                    {phase === "checking" && "Checking..."}
                </p>
            <div className="matix-grid">
                {view.colors.map((color) => (
                    <button 
                    key = {color} 
                    className={`matrix-tile ${lit === color? "lit" : ""}`}
                    style={{background:color}}
                    onClick={() => handleTap(color)}
                    disabled ={phase !== "input"}
                />
                ))}
            </div>
            {<p className = "challenge-feedback">{feedback}</p>}
            </div>
        </div>
    );
}