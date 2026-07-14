import { useState } from "react";
import { createGame } from "./api";

interface CreateGameProps {
  onCreated: (gameId: string, yourId: string, seatIds: string[]) => void;
}

export function CreateGame({ onCreated }: CreateGameProps) {
  const [seatCount, setSeatCount] = useState(2);
  const [yourName, setYourName] = useState("you");
  const [botNames, setBotNames] = useState(["bot1"]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [created, setCreated] = useState<{ gameId: string; seatIds: string[] } | null>(null);

  const otherSeatCount = seatCount - 1;
  // Derive per-index with a fallback, rather than slicing + padding —
  // botNames can have gaps (e.g. the user edits seat 3's name without ever
  // touching seat 2's), and slicing a short/sparse array carries `undefined`
  // through into the request body instead of filling in a default name.
  const seatIds = [
    yourName || "you",
    ...Array.from({ length: otherSeatCount }, (_, i) => botNames[i] || `bot${i + 1}`),
  ];

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const { game_id } = await createGame(seatIds);
      setCreated({ gameId: game_id, seatIds });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  if (created) {
    const botSeats = created.seatIds.slice(1).map((id) => `${id}:random`).join(" ");
    const watchCommand = `love_letter watch --game-id ${created.gameId} --bots ${botSeats}`;
    return (
      <div style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
        <h1>Game created</h1>
        <p>Run this in a terminal to bring the bot seats to life:</p>
        <pre style={{ background: "#222", color: "#eee", padding: 12, borderRadius: 8 }}>
          {watchCommand}
        </pre>
        <button onClick={() => onCreated(created.gameId, created.seatIds[0], created.seatIds)}>
          Enter game
        </button>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 480, margin: "4rem auto", fontFamily: "sans-serif" }}>
      <h1>Love Letter</h1>
      <form onSubmit={handleSubmit}>
        <label>
          Players (2-6):{" "}
          <input
            type="number"
            min={2}
            max={6}
            value={seatCount}
            onChange={(e) => setSeatCount(Number(e.target.value))}
          />
        </label>
        <div style={{ marginTop: 12 }}>
          <label>
            Your name:{" "}
            <input value={yourName} onChange={(e) => setYourName(e.target.value)} />
          </label>
        </div>
        {Array.from({ length: otherSeatCount }).map((_, i) => (
          <div key={i} style={{ marginTop: 8 }}>
            <label>
              Bot seat {i + 1} name:{" "}
              <input
                value={botNames[i] ?? `bot${i + 1}`}
                onChange={(e) => {
                  const next = [...botNames];
                  next[i] = e.target.value;
                  setBotNames(next);
                }}
              />
            </label>
          </div>
        ))}
        <button type="submit" disabled={busy} style={{ marginTop: 16 }}>
          {busy ? "Creating..." : "Create game"}
        </button>
      </form>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
    </div>
  );
}
