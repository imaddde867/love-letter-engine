export interface PlayerState {
  id: string;
  is_active: boolean;
  hand_card: number | null;
  favor_tokens: number;
  drawn_card?: number | null;
}

export interface PlayedCard {
  player_id: string;
  card: string;
  target_player: string | null;
}

export interface GameState {
  game_id: string;
  round: number;
  deck_remaining: number;
  favor_token_threshold: number;
  players: PlayerState[];
  current_player_index: number;
  current_player_id: string | null;
  played_cards: PlayedCard[];
  your_id: string;
}

export interface LegalAction {
  action_type: string;
  card_in_hand: number;
  other_card: number | null;
  player_id: string;
  target_player: string | null;
  guess: number | null;
}

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail?.message ?? body.detail ?? `Request failed: ${response.status}`);
  }
  return response.json();
}

export function createGame(
  playerIds: string[],
): Promise<{ game_id: string; tokens: Record<string, string> }> {
  return request("/games", {
    method: "POST",
    body: JSON.stringify({ player_ids: playerIds }),
  });
}

export function getState(gameId: string, playerId: string, token: string): Promise<GameState> {
  return request(
    `/games/${gameId}?player_id=${encodeURIComponent(playerId)}&token=${encodeURIComponent(token)}`,
  );
}

export function getLegalActions(
  gameId: string,
  playerId: string,
  token: string,
): Promise<LegalAction[]> {
  return request(
    `/games/${gameId}/actions?player_id=${encodeURIComponent(playerId)}&token=${encodeURIComponent(token)}`,
  );
}

export function postAction(
  gameId: string,
  action: LegalAction,
  token: string,
): Promise<GameState> {
  return request(`/games/${gameId}/actions`, {
    method: "POST",
    body: JSON.stringify({ ...action, token }),
  });
}
