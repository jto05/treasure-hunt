import './RegisterForm.css'
import { useState } from "react";

export default function RegisterForm({onSuccess}){
    const [name, setName] = useState(""); // what use types
    const [error, setError] = useState("");

    async function handleSubmit(event){
        event.preventDefault(); // to stop the page from reloading
        setError("");

        const res = await fetch("/api/team", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name}),
        });

        const data = await res.json();

        if (res.ok) onSuccess();
        else if (res.status === 409) setError("That name is taken.");
        else if (data.error === "bad_name") setError("Enter a name (30 characters max).");
        else if (data.error === "mac_not_found") setError("Couldn't identify your device. Are you on the hunt Wi-Fi?");
        else setError("Something went wrong.");
    }

    // display
    return (
    <div className="register">
        <form className="register-card" onSubmit={handleSubmit}>
            <h1 className="register-title">Treasure Hunt</h1>
            <input
            className="register-input"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Team name"
            />
            <button className="register-button" type="submit">Join</button>
            {error && <p className="register-error">{error}</p>}
        </form>
    </div>
  );
}