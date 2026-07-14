import { useEffect, useRef, useState } from "react";
import { getLegalActions, getState, postAction, type GameState, type LegalAction } from "./api";
import { Card } from "./Card";
import { cardLabel } from "./cards";

interface GameViewProps {
  gameId: string;
  yourId: string;
}

const POLL_MS = 1200;

function describeAction(action: LegalAction): string {
  const played = cardLabel(action.card_in_hand);
  const parts = [`Play ${played}`];
  if (action.target_player) parts.push(`-> ${action.target_player}`);
  if (action.guess != null) parts.push(`guess ${cardLabel(action.guess)}`);
  if (action.other_card != null) parts.push(`(keep ${cardLabel(action.other_card)})`);
  return parts.join(" ");
}

export function GameView({ gameId, yourId }: GameViewProps) {
  const [state, setState] = useState<GameState | null>(null);
  const [actions, setActions] = useState<LegalAction[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  // A poll in flight when the user clicks an action can resolve *after*
  // postAction does, resurrecting stale legal-action buttons for a turn
  // that's already over. The ref (not the `submitting` state, which the
  // poll closure would only see as of its own render) lets poll() skip
  // applying a response that raced a submission.
  const submittingRef = useRef(false);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      try {
        const next = await getState(gameId, yourId);
        if (cancelled || submittingRef.current) return;
        setState(next);
        setError(null);

        if (next.current_player_id === yourId) {
          const legal = await getLegalActions(gameId, yourId);
          if (!cancelled && !submittingRef.current) setActions(legal);
        } else {
          setActions([]);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : String(err));
      }
    }

    poll();
    const timer = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [gameId, yourId]);

  if (error) return <p style={{ color: "crimson" }}>{error}</p>;
  if (!state) return <p>Loading...</p>;

  const winner = state.players.find((p) => p.favor_tokens >= state.favor_token_threshold);

  async function choose(action: LegalAction) {
    submittingRef.current = true;
    setSubmitting(true);
    try {
      const next = await postAction(gameId, action);
      setState(next);
      setActions([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      submittingRef.current = false;
      setSubmitting(false);
    }
  }

  return (
    <div style={{ maxWidth: 900, margin: "2rem auto", fontFamily: "sans-serif" }}>
      <h1>Love Letter — round {state.round}</h1>
      <p>Deck remaining: {state.deck_remaining} | Favor threshold: {state.favor_token_threshold}</p>

      {winner && (
        <h2 style={{ color: "gold" }}>{winner.id} wins the game!</h2>
      )}

      <div style={{ display: "flex", gap: 24, flexWrap: "wrap", marginTop: 24 }}>
        {state.players.map((player) => (
          <div
            key={player.id}
            style={{
              padding: 12,
              borderRadius: 12,
              background: player.id === state.current_player_id ? "#333" : "transparent",
              opacity: player.is_active ? 1 : 0.5,
              textAlign: "center",
            }}
          >
            <div style={{ fontWeight: player.id === yourId ? "bold" : "normal" }}>
              {player.id} {player.id === yourId && "(you)"}
            </div>
            <Card value={player.hand_card} size="md" showInfo={player.id === yourId} />
            <div>Favor: {player.favor_tokens}</div>
            {!player.is_active && <div>Eliminated</div>}
            {player.id === state.current_player_id && player.is_active && <div>Their turn</div>}
          </div>
        ))}
      </div>

      {actions.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3>Your move</h3>
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {actions.map((action, i) => (
              <button key={i} disabled={submitting} onClick={() => choose(action)}>
                {describeAction(action)}
              </button>
            ))}
          </div>
        </div>
      )}

      <div style={{ marginTop: 32 }}>
        <h3>Played cards</h3>
        <ul>
          {state.played_cards
            .slice()
            .reverse()
            .map((entry, i) => (
              <li key={i}>
                {entry.player_id} played {entry.card}
                {entry.target_player ? ` -> ${entry.target_player}` : ""}
              </li>
            ))}
        </ul>
      </div>
    </div>
  );
}
