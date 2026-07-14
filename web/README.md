# Love Letter GUI

React + Vite spectator/player GUI for the Love Letter engine's HTTP API.

## Setup

```bash
npm install
npm run dev
```

Dev server runs at `http://localhost:5173`. It talks to the backend API at
`http://127.0.0.1:8000` by default; override with a `VITE_API_URL` env var
(see `src/api.ts`).

## Running against a game

1. Start the backend API server from the repo root:

   ```bash
   python -m love_letter serve
   ```

2. Create a game and drive it with bots (or leave seats for humans) using the
   `watch` CLI command, which exercises the same HTTP API the GUI uses:

   ```bash
   python -m love_letter watch --bots random greedy
   ```

   This prints the new `game_id` and streams moves as they happen.

3. Point the GUI at that `game_id` (via `CreateGame.tsx` or the URL, per the
   app's UI) to spectate or play through the browser.

To attach the driver to a game the GUI already created instead, pass
`--game-id <id>` along with `seat_id:strategy` bot assignments — see
`python -m love_letter watch --help`.
