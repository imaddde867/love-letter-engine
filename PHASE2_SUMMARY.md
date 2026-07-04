# Phase 2: API Layer — Summary

## What Was Built

### 1. Pydantic-Compatible Action Model
- Converted `Action` from dataclass to `BaseModel`
- Enables direct JSON parsing from API requests
- Maintains backward compatibility with engine

### 2. REST API Endpoints
Created `love_letter/api/` package with FastAPI:

**Endpoints:**
- `POST /games` — Create new game (returns 201)
- `GET /games/{game_id}` — Get state for player
- `POST /games/{game_id}/actions` — Execute action

**Features:**
- Pydantic request/response validation
- Structured error handling (400, 404, 422)
- Game state serialization to JSON

### 3. Engine Fixes

**Handmaid Protection Tracking:**
- Added `protected_until_next_turn` flag to Player
- Handmaid effect sets protection flag
- Guard, Baron, King, Prince effects check protection before targeting
- Protection clears at start of protected player's turn

**Spy Bonus:**
- Implemented Spy bonus awarding at round end
- Only one active player who played a Spy gets extra favor token
- No bonus if multiple players played Spies

## Test Coverage

**95 tests passing** (up from 76 in Phase 1):
- 4 new Pydantic Action tests
- 4 API games endpoint tests
- 4 API actions endpoint tests
- 2 full game flow tests
- 3 Handmaid protection tests
- 2 Spy bonus tests

## Files Changed

**New files:**
- `love_letter/api/__init__.py`
- `love_letter/api/app.py` (FastAPI app)
- `love_letter/api/schemas.py` (Pydantic schemas)
- `tests/test_action_pydantic.py`
- `tests/test_api_games.py`
- `tests/test_api_actions.py`
- `tests/test_api_full_game.py`
- `tests/test_handmaid_protection.py`
- `tests/test_spy_bonus.py`

**Modified files:**
- `love_letter/models/action.py` — Pydantic BaseModel
- `love_letter/models/player.py` — Added protection flag
- `love_letter/engine/engine.py` — Protection clearing, Spy bonus
- `love_letter/engine/effects/guard.py` — Check protection
- `love_letter/engine/effects/baron.py` — Check protection
- `love_letter/engine/effects/king.py` — Check protection
- `love_letter/engine/effects/prince.py` — Check protection
- `love_letter/engine/effects/handmaid.py` — Set protection

## API Examples

**Create Game:**
```bash
curl -X POST http://localhost:8000/games \
  -H "Content-Type: application/json" \
  -d '{"player_ids": ["alice", "bob"]}'
```

**Get State:**
```bash
curl "http://localhost:8000/games/{game_id}?player_id=alice"
```

**Execute Action:**
```bash
curl -X POST "http://localhost:8000/games/{game_id}/actions" \
  -H "Content-Type: application/json" \
  -d '{
    "player_id": "alice",
    "action_type": "play_card",
    "card_in_hand": 4,
    "other_card": 9
  }'
```

## Next Steps (Phase 3)

- Bot interface (stateless functions)
- Simulator for bot-vs-bot tournaments
- Example bots (random, heuristic)
- CLI commands (`python -m love_letter test`, `serve`)
