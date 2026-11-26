import './Distances.css'
import { useEffect, useState} from "react";
import Leaderboard from "./Leaderboard";

// change to be on theme later
const LABELS = {
    here: "Here at node",
    hot: "Hot",
    warm: "Warm",
    cool: "Cool",
    cold: "Cold",
};

//make time appear as format MM:SS
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, "0")}`; 
}

export default function Distances({onNotRegistered, onStartChallenge}){
    const [state, setState] = useState(null);

    useEffect(() => {
        let canceled = false;

        async function poll(){ // poll is used to update every few seconds
            try{
                const res = await fetch("/api/state");
                if (res.status === 401) return onNotRegistered?.(); // no cookie
                const data = await res.json();
                if(!canceled) setState(data);
            } catch {
                // empty on purpose, if fails it should just try again
            }
        }

        poll();
        const id = setInterval(poll, 2000);
        return () => { //when page switches, clean up!
            canceled = true;
            clearInterval(id);
        };
    }, [onNotRegistered]);

    async function handleAdvance(){
        const res = await fetch("/api/advance", {method: "POST"});
        if (res.status === 401) return onNotRegistered?.();
        const next = await fetch("/api/state");
        if(next.ok) setState(await next.json());
    }

    if (!state) return <p>Loading...</p>;

    const { team, progress, node, distance } = state;

    if (node === null) {
        return(
        <div className="endScreen">
            <div className="endScreen-card">
                <h2 className="endScreen-text">{team}, you finished the treasure hunt in {formatTime(progress.seconds)}</h2>
                <Leaderboard myTeam={team} />
            </div>
        </div>
        )
    }

    // display
    return (
        <div className="distances">
            <form className="distances-card">
                <h2 className="distances-title">Team {team}</h2>
                <p className="distances-key">Node {progress.step + 1} of {progress.total}</p>
                <p className="distances-progress">
                    <strong>Head to node {node}:</strong>{" "}
                    {distance.status === "ok"
                        ? `${LABELS[distance.level]}`
                        : "No signal"}
                </p>
                {distance.in_range && (
                    <button className="advance-button" onClick={onStartChallenge}>I'm here!</button>
                )}
            </form>
        </div>
    );
}