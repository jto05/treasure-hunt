import { useEffect, useState} from "react";

// change to be on theme later
const LABEL = {
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

    if (!state) return <p>Loading...</p>;

    // display
    return (
        <div>
            <h2>Team {state.team}</h2>
            {Object.entries(state.nodes).map(([node, info]) => (
                <div key={node}>
                    <strong>Node {node}:</strong>{" "}
                    {info.status === "ok"
                        ? `${LABELS[info.level]} (~${info.meters} m)`
                        : "No signal"}
                </div>
            ))}
        </div>
    );
}