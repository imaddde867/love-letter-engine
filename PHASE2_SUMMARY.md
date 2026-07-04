# Phase 2: API Layer Summary

## What Was Built

### Pydantic-Compatible Action Model

- Converted `Action` to a Pydantic `BaseModel`.
- Keeps the engine interface usable from JSON request bodies.

### REST API Layer

Created `love_letter/api/` with:

- `POST /games` - create a game.
- `GET /games/{game_id}` - get state for a requesting player.
- `POST /games/{game_id}/actions` - execute an action and return updated state.

The state response includes:

- `game_id`
- `round`
- `deck_remaining`
- `favor_token_threshold`
- `players`
- `played_cards`
- `your_id`

For the requesting player, `players[*].drawn_card` exposes the next card needed to submit a valid action.

### Engine Fixes

- Handmaid protection tracking and clearing.
- Targeting effects respect Handmaid protection.
- Spy bonus at round end.
- Chancellor card-loss regression fixed.
- Guard/Priest/Baron/King/Prince target validation restored.
- Guard guess validation restored.
- Non-Chancellor actions reject impossible client-submitted card pairs.
- Played-card history now records `target_player` where applicable.

## Test Coverage

Current suite:

- API game/action/state tests.
- Pydantic action tests.
- Card effect tests.
- Validation tests.
- Handmaid protection tests.
- Spy bonus tests.
- Chancellor regression tests.
- Property tests.

Verification:

```bash
.venv/bin/python -m pytest -q
```

Result: `115 passed in 0.79s`.

## Phase 3 Next Steps

- Bot interface.
- Legal-action generation, including `available_actions`.
- Bot-vs-bot simulator.
- Example bots.
- CLI polish.
