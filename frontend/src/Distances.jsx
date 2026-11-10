import { useEffect, useState} from "react";

// change to be on theme later
const LABELS = {
    here: "Here at node",
    hot: "Hot",
    warm: "Warm",
    cool: "Cool",
    cold: "Cold",
};

export default function Distances({onNotRegistered}){
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
        return <h2>{team}, you finished the hunt! 🏆</h2>;
    }

    // display
    return (
        <div>
            <h2>Team {team}</h2>
            <p>Node {progress.step + 1} of {progress.total}</p>
            <p>
                <strong>Head to node {node}:</strong>{" "}
                {distance.status === "ok"
                    ? `${LABELS[distance.level]} (~${distance.meters} m)`
                    : "No signal"}
            </p>
            {distance.in_range && (
                <button onClick={handleAdvance}>At Node! Next node</button>
            )}
        </div>
    );
}