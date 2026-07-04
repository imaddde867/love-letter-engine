# Agents — Love Letter Engine

This repository contains a robust backend engine for the Love Letter card game, designed for bot training, simulation, and future TUI/GUI integration.

## For Agents

If you're an agent (bot, LLM, or automated system) interacting with this engine:

### How to Play

1. **Create a game**: `POST /games` with your player ID
2. **Get state**: `GET /games/{game_id}?player_id=your_id` after each action
3. **Take turns**: `POST /games/{game_id}/actions` with your action

### Action Format

```json
{
  "player_id": "your_bot_id",
  "action_type": "play_card",
  "card_in_hand": "Guard",
  "other_card": "Priest",
  "target_player": "opponent_id",
  "guess": "Priest"
}
```

### Game State Response

You'll receive full state including:
- Deck count remaining
- All players (active status only, no hidden hands)
- Played cards with targets (for deduction)
- Your player ID

### Strategy Tips

- Track played cards for deduction
- Guard is stronger late-game (fewer unknown cards)
- Handmaid protects valuable hands
- Prince can save you from weak hands or remove strong ones
- Countess discard rule reveals information indirectly

## For Developers

See `PLAN.md` for implementation phases and `CONTEXT.md` for domain terminology.

### Running Locally

```bash
# Run a test game with example bots
python -m love_letter test --bots random heuristic

# Start the API server
python -m love_letter serve --host 0.0.0.0 --port 8000

# Run tests
pytest tests/ -v
```

### Architecture

- **Engine**: Class-based, in-memory, no persistence (V1)
- **API**: FastAPI, REST, reactive flow
- **Testing**: pytest + hypothesis (property-based)
- **Bot Interface**: Stateless functions

## API Documentation

Interactive docs at: `http://localhost:8000/docs`

## License

Private repository. All rights reserved.
