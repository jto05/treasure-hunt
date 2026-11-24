import { useEffect, useState } from "react";
import "./Leaderboard.css";

//make time appear as format MM:SS
function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${String(s).padStart(2, "0")}`; 
}

export default function Leaderboard({ myTeam }) {
    const [rows, setRows] = useState(null);

    useEffect(() => {
        let cancelled = false;

        async function load() {
            try {
                const res = await fetch("/api/leaderboard");
                if (!res.ok) {
                    throw new Error("Failed to load leaderboard");
                }
                const data = await res.json();
                if (!cancelled) setRows(data.leaderboard.filter((r) => r.finished));
            } catch (err) {
                console.error("leaderboard failed:", err);
                // do nothing
            }
        }

        load();
        const id = setInterval(load, 5000); //auto reload
        return () => {
            cancelled = true;
            clearInterval(id);
        };
    }, []);

    if (!rows) return <p>Loading leaderboard...</p>;

    return (
        <div className="leaderboard">
            <h3 className="leaderboard-title">Leaderboard</h3>
            {rows.length === 0 && <p>No teams have finished yet.</p>}
            <ol className="leaderboard-list">
                {rows.map((r) => (
                <li key={r.team} className={r.team === myTeam ? "leaderboard-row mine" : "leaderboard-row"}>
                    <span className="leaderboard-name">{r.team}</span>
                    <span className="leaderboard-time">{formatTime(r.seconds)}</span>
                </li>
                ))}
            </ol>
        </div>
    );
}