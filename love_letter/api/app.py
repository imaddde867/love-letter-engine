"""FastAPI application for the Love Letter engine."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from love_letter.api.schemas import ActionRequest, CreateGameRequest
from love_letter.engine.engine import Engine
from love_letter.engine.errors import GameOverError
from love_letter.engine.legal_actions import available_actions
from love_letter.models.action import Action
from love_letter.models.state import GameState

engine = Engine()


def _card_value(card):
    """Return the card's value, or None if there is no card."""
    return card.value if card is not None else None


def _state_to_dict(state: GameState, player_id: str) -> dict:
    """Convert GameState to a JSON-serializable dict for the API response."""
    current_player_id = state.current_player_id
    players = []
    for pid, player in state.players.items():
        # Hand cards are hidden except to their own player. Eliminated
        # players' hands are public per the rules ("discard your hand faceup").
        visible_hand = pid == player_id or not player.is_active
        player_state = {
            "id": pid,
            "is_active": player.is_active,
            "hand_card": _card_value(player.hand_card) if visible_hand else None,
            "favor_tokens": player.favor_tokens,
        }
        # The drawn card only exists once it's actually been drawn — reveal
        # it to its owner only on their own turn, not the deck's future top
        # card while someone else is still acting.
        if pid == player_id and pid == current_player_id:
            player_state["drawn_card"] = _card_value(
                state.deck[0] if state.deck else state.facedown_card
            )
        players.append(player_state)

    played_cards = [
        {
            "player_id": entry["player_id"],
            "card": entry["card"].display_name,
            "target_player": entry.get("target_player"),
        }
        for entry in state.played_cards
    ]

    return {
        "game_id": state.game_id,
        "round": state.round,
        "deck_remaining": state.deck_count,
        "favor_token_threshold": state.favor_token_threshold,
        "players": players,
        "current_player_index": state.current_player_index,
        "current_player_id": state.current_player_id,
        "played_cards": played_cards,
        "your_id": player_id,
    }


app = FastAPI(title="Love Letter Engine", version="0.1.0")

# Local hobby project: the GUI (Vite dev server) runs on a different port
# than this API, so the browser needs CORS to fetch across origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/games", status_code=201)
async def create_game(request: CreateGameRequest):
    """Create a new game."""
    if len(request.player_ids) < 2 or len(request.player_ids) > 6:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_request",
                "message": "Player count must be between 2 and 6",
            },
        )

    game_id = engine.create_game(request.player_ids)
    return {"game_id": game_id}


@app.get("/games/{game_id}")
async def get_state(game_id: str, player_id: str = Query(...)):
    """Get the current game state for a specific player."""
    try:
        state = engine.get_state(game_id, player_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    return _state_to_dict(state, player_id)


@app.get("/games/{game_id}/actions")
async def get_legal_actions(game_id: str, player_id: str = Query(...)):
    """List the legal actions ``player_id`` can currently take."""
    try:
        state = engine.get_state(game_id, player_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Game not found")

    if player_id != state.current_player_id:
        return []

    return [action.model_dump() for action in available_actions(state, player_id)]


@app.post("/games/{game_id}/actions")
async def execute_action(game_id: str, request: ActionRequest):
    """Execute an action for a player in a game."""
    action = Action.model_validate(request, from_attributes=True)

    try:
        state = engine.execute_action(game_id, request.player_id, action)

        # A round just ended (tokens awarded) but nobody hit the favor
        # threshold yet — deal the next round so the game can continue.
        if not engine._is_game_over(state) and engine._is_round_over(state):
            engine._start_new_round(state)

        return _state_to_dict(state, request.player_id)

    except KeyError as e:
        message = str(e).strip('"')
        if message.startswith("Game "):
            raise HTTPException(status_code=404, detail=message)
        raise HTTPException(status_code=400, detail=message)

    except GameOverError as e:
        raise HTTPException(
            status_code=409,
            detail={"error": "game_over", "message": str(e)},
        )

    except Exception as e:
        # Return structured error for API consumers
        if hasattr(e, "violations") and e.violations:
            violations = [v.message for v in e.violations]
            return JSONResponse(
                status_code=400,
                content={
                    "error": "invalid_action",
                    "message": "One or more validation violations",
                    "violations": violations,
                },
            )
        raise HTTPException(status_code=400, detail=str(e))
