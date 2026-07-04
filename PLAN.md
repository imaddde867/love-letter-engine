# Love Letter Engine — Implementation Plan

## Overview

A robust, clean backend engine for Love Letter that supports:
- Bot-vs-bot simulation for training
- HTTP API for future TUI/GUI
- Property-based testing for correctness
- Extensible architecture for LLM/bot integration

## Architecture Decisions

See `docs/adr/` for full details on each decision.

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Language | Python + FastAPI | Your stack, great for AI/ML later |
| API Style | REST + Reactive | Simple, debuggable, works with curl |
| Engine Design | Class-based | Encapsulates state, scales to multiple games |
| Card Effects | Strategy Pattern | Testable, extensible, Open/Closed Principle |
| Error Handling | Strict validation | Prevents corruption, clear bot feedback |
| Testing | Property + Unit | Catches edge cases, safe refactoring |
| Persistence | None (V1) | In-memory only, add later if needed |
| Bot Interface | Stateless functions | Simple, testable, no state sync issues |

## Project Structure

```
love_letter/
├── pyproject.toml
├── README.md
├── CONTEXT.md
├── PLAN.md
├── docs/adr/
│   ├── 0001-class-based-engine.md
│   ├── 0002-strategy-pattern-for-card-effects.md
│   ├── 0003-rest-reactive-api.md
│   ├── 0004-strict-validation-with-violations.md
│   └── 0005-property-based-testing-strategy.md
├── love_letter/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── models/
│   │   ├── __init__.py
│   │   ├── card.py              # Card enum with metadata
│   │   ├── player.py            # Player dataclass
│   │   ├── action.py            # Action dataclass
│   │   └── state.py             # GameState dataclass
│   ├── engine/
│   │   ├── __init__.py
│   │   ├── engine.py            # Engine class
│   │   ├── rules.py             # Validation logic
│   │   └── effects/
│   │       ├── __init__.py
│   │       ├── guard.py
│   │       ├── priest.py
│   │       ├── baron.py
│   │       ├── handmaid.py
│   │       ├── prince.py
│   │       ├── chancellor.py
│   │       ├── king.py
│   │       ├── countess.py
│   │       ├── princess.py
│   │       └── spy.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── app.py               # FastAPI app
│   │   ├── routes.py            # Endpoint handlers
│   │   └── schemas.py           # Pydantic models
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── base.py              # Bot interface
│   │   └── examples/
│   │       ├── __init__.py
│   │       ├── random_bot.py
│   │       └── heuristic_bot.py
│   └── simulation/
│       ├── __init__.py
│       └── simulator.py
└── tests/
    ├── __init__.py
    ├── test_card.py
    ├── test_player.py
    ├── test_action.py
    ├── test_engine.py
    ├── test_rules.py
    ├── test_properties.py
    └── test_api.py
```

## Implementation Phases

### Phase 1: Core Engine + Tests

**Models:**
- `GameId`: Type alias for `str` (unique game identifier)
- `Card` enum with name, value, count
- `Player` dataclass with id, is_active, hand_card, favor_tokens, cards_played
- `Action` dataclass with action_type, card_in_hand, other_card, target_player, guess
- `GameState` dataclass with game_id, round, deck, facedown_card, players, current_player_index, played_cards, favor_token_threshold

**Engine:**
- `create_game(player_ids: list[str]) -> GameId`
- `get_state(game_id: GameId, player_id: str) -> GameState`
- `execute_action(game_id: GameId, action: Action) -> GameState`
- Turn flow: validate → execute → check round end → check game end → advance player
- Game ends when a player reaches favor_token_threshold

**Card Effects (one per file):**
- Guard: target + guess, eliminate if match
- Priest: target, reveal hand card to actor
- Baron: target, compare values, lower eliminated
- Handmaid: self-protection until next turn
- Prince: any target (including self), discard and redraw
- Chancellor: draw 2, keep 1, return 2 to bottom
- King: target, swap hands
- Countess: discard rule (must play if holding King/Prince)
- Princess: discard = elimination
- Spy: track played spies, bonus token if only one

**Tests:**
- Unit tests for each card effect
- Property tests: "round always ends", "valid moves preserve state"
- Integration tests: full game flows

### Phase 2: API Layer

**Endpoints:**
- `POST /games` — create game
- `GET /games/{game_id}` — get state for player
- `POST /games/{game_id}/actions` — execute action

**Pydantic Models:**
- `CreateGameRequest`: player_ids, player_count (optional, auto-calculated)
- `ActionRequest`: player_id, action_type, card_in_hand, other_card, target_player, guess
- `GameStateResponse`: full state with your_id, favor_token_threshold

**Error Handling:**
- `400 Bad Request` with violations list for invalid actions
- `404 Not Found` for missing games

### Phase 3: Bot Interface + Simulation

**Bot Interface:**
```python
def my_bot(state: BotState) -> BotAction:
    # state contains game state visible to bot
    # return action
```

**Simulator:**
```python
class Simulator:
    def run_game(self) -> GameState
    def run_tournament(self, num_games: int) -> dict[str, int]
```

**Example Bots:**
- Random: pick random valid action
- Heuristic: always play Guard with random guess

### Phase 4: Polish

- Error handling edge cases
- Documentation (docstrings + README)
- Performance profiling
- CLI: `python -m love_letter test`, `python -m love_letter serve`

## Key API Contracts

### Game State Response
```json
{
  "game_id": "abc123",
  "round": 3,
  "deck_remaining": 8,
  "favor_token_threshold": 4,
  "players": [{"id": "bot_1", "is_active": true, "hand_card": null}],
  "played_cards": [{"player_id": "bot_1", "card": "Guard", "target_player": "bot_2"}],
  "your_id": "bot_1",
  "available_actions": ["play"]
}
```

### Action Request
```json
{
  "player_id": "bot_1",
  "action_type": "play_card",
  "card_in_hand": "Guard",
  "other_card": "Priest",
  "target_player": "bot_2",
  "guess": "Priest"
}
```

**Note:** `target_player` is required for cards that target (Guard, Priest, Baron, King). Omit for non-targeting cards (Handmaid, Prince on self, Countess, Princess, Chancellor, Spy).
```

### Error Response (400)
```json
{
  "error": "invalid_action",
  "message": "Guard requires a target_player and guard_guess",
  "violations": ["missing_field: target_player"]
}
```

## Testing Approach

**Property Tests (hypothesis):**
```python
@given(st.lists(st.text(), min_size=2, max_size=6))
def test_round_always_ends(players):
    game_id = engine.create_game(players)
    state = engine.get_state(game_id, players[0])
    while not state.is_round_over():
        action = make_random_valid_action(state, players[0])
        state = engine.execute_action(game_id, action)
    assert state.is_round_over()
```

**Unit Tests:**
```python
def test_guard_correct_guess_eliminates():
    # Setup game with known hands
    # Play Guard with correct guess
    # Assert target is eliminated
```

## CLI Commands

```bash
# Run a test game
python -m love_letter test --bots random heuristic

# Start API server
python -m love_letter serve --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v

# Check coverage
pytest --cov=love_letter/engine tests/
```

## Success Criteria

- [ ] All 21 card effects implemented and tested
- [ ] Property tests pass for all game invariants
- [ ] API endpoints work with curl
- [ ] Bot-vs-bot simulation runs full games
- [ ] Error handling returns specific violations
- [ ] Documentation complete (docstrings + README)
- [ ] Code is clean, minimal, and well-organized

## Next Steps

1. Set up project structure (`pyproject.toml`, directories)
2. Implement models (`Card`, `Player`, `Action`, `GameState`)
3. Implement engine core (`create_game`, `execute_action`)
4. Write unit tests for models
5. Implement card effects one by one
6. Add API layer
7. Add bot interface and simulation
8. Polish and document
