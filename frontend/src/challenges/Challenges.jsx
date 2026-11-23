//challenges.jsx
import { useEffect, useState } from "react";
import Trivia from "./Trivia.jsx";
import MemoryMatrix from "./MemoryMatrix.jsx";
import DistThreshold from "./DistThreshold.jsx";
import TimebankTrivia from "./TimebankTrivia.jsx";

const GAMES = {
    trivia: Trivia,
    memory_matrix: MemoryMatrix,
    dist_threshold: DistThreshold,
    timebank_trivia: TimebankTrivia,
};

export default function Challenges({ onDone, onNotRegistered }) {
    const [node, setNode] = useState(null); //the node player is on
    const [challenge, setChallenge] = useState(null); //whatever start() returned
    
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

    if (!challenge) return <p>Loading challenge...</p>;
    const Game = GAMES[challenge.type];

    return (
        <Game
            challenge={challenge}
            node={node}
            onDone={onDone}
            onNotRegistered={onNotRegistered}
        />
    );
}