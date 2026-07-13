# Love Letter Engine

A robust, clean backend engine for the Love Letter card game.

## Features

- **Bot-ready**: Stateless API design perfect for training and simulation
- **Property-tested**: Game rules validated with hypothesis
- **Fast**: In-memory engine, no database overhead
- **Extensible**: Strategy Pattern for card effects, easy to add new cards

## Quick Start

```bash
# Run a test game
python -m love_letter test

# Run a test game with specific bots (random, greedy, spy)
python -m love_letter test --bots random greedy

# Start API server
python -m love_letter serve

# Run tests
pytest tests/ -v
```

## Architecture

```
love_letter/
├── engine/          # Core game logic
├── api/             # FastAPI HTTP layer
├── bots/            # Bot interface and examples
└── simulation/      # Bot-vs-bot simulation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/games` | Create a new game |
| GET | `/games/{id}` | Get game state |
| POST | `/games/{id}/actions` | Execute an action |

Interactive docs: `http://localhost:8000/docs`

## Development

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests with coverage
pytest --cov=love_letter tests/
```

## Documentation

- [CONTEXT.md](./CONTEXT.md) — Domain glossary
- [PLAN.md](./PLAN.md) — Implementation plan
- [docs/adr/](./docs/adr/) — Architecture decision records

## License

Private. All rights reserved.
