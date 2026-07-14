"""CLI entry point for the Love Letter engine.

Provides three subcommands:
- ``test``: run a bot-vs-bot simulation and print the result.
- ``serve``: start the FastAPI HTTP server via uvicorn.
- ``watch``: create a game on a running server and drive it over HTTP,
  printing moves as they happen. Unlike ``test``, this exercises the real
  API boundary (bots only see what the API exposes) and is meant to be
  paired with a GUI pointed at the same game_id for spectating/playing.
"""

from __future__ import annotations

import argparse
import sys

from love_letter.bots import Player
from love_letter.bots.examples import GreedyBot, RandomBot, SpyBot
from love_letter.models.card import CardType
from love_letter.simulation import simulate

_BOT_FACTORIES: dict[str, type[Player]] = {
    "random": RandomBot,
    "greedy": GreedyBot,
    "heuristic": GreedyBot,
    "spy": SpyBot,
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="love_letter")
    subparsers = parser.add_subparsers(dest="command")

    test_parser = subparsers.add_parser("test", help="Run a bot-vs-bot simulation")
    test_parser.add_argument(
        "--bots",
        nargs=2,
        default=["random", "random"],
        metavar=("BOT_A", "BOT_B"),
        choices=sorted(_BOT_FACTORIES),
        help=f"Two bot names from: {', '.join(sorted(_BOT_FACTORIES))}",
    )
    test_parser.add_argument(
        "--players",
        type=int,
        default=4,
        help="Total number of players (2-6, split evenly between the two bots)",
    )

    serve_parser = subparsers.add_parser("serve", help="Start the HTTP API server")
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8000)

    watch_parser = subparsers.add_parser(
        "watch",
        help="Drive a game over HTTP — creates a new game, or attaches to an "
        "existing one (e.g. one a GUI created) with --game-id",
    )
    watch_parser.add_argument(
        "--url", default="http://127.0.0.1:8000", help="Base URL of a running `serve`"
    )
    watch_parser.add_argument(
        "--game-id",
        default=None,
        help="Attach to an existing game instead of creating a new one. "
        "Requires --bots entries in 'seat_id:strategy:token' form.",
    )
    watch_parser.add_argument(
        "--bots",
        nargs="+",
        default=["random", "random"],
        help=(
            "Without --game-id: one strategy per seat (2-6 seats), creating "
            f"seats p0..pN — e.g. 'random greedy'. Strategies: "
            f"{', '.join(sorted(_BOT_FACTORIES))}, or 'human' to leave a seat "
            "unplayed. With --game-id: 'seat_id:strategy:token' triples for "
            "the seats you want this process to control (token as issued by "
            "the game's creator), e.g. 'bot1:random:abc123 bot2:greedy:def456'."
        ),
    )
    watch_parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Seconds between moves, for spectator pacing",
    )

    return parser


def _run_test(args: argparse.Namespace) -> int:
    bot_a_name, bot_b_name = args.bots
    bot_a = _BOT_FACTORIES[bot_a_name]()
    bot_b = _BOT_FACTORIES[bot_b_name]()

    result = simulate(bot_a, bot_b, player_count=args.players)

    print(f"Winner: {result.winner_id}")
    print(f"Total rounds: {result.total_rounds}")
    print(f"Final standings: {result.final_standings}")
    if result.error:
        print(f"Error: {result.error}")
        return 1
    return 0


def _run_serve(args: argparse.Namespace) -> int:
    import uvicorn

    uvicorn.run("love_letter.api.app:app", host=args.host, port=args.port)
    return 0


def _run_watch(args: argparse.Namespace) -> int:
    import httpx

    from love_letter.driver import STRATEGIES, drive_game

    attaching = args.game_id is not None

    if attaching:
        bot_assignments: dict[str, str] = {}
        tokens: dict[str, str] = {}
        for entry in args.bots:
            parts = entry.split(":", 2)
            if len(parts) != 3:
                print(
                    f"--game-id requires 'seat_id:strategy:token' entries, "
                    f"got '{entry}'",
                    file=sys.stderr,
                )
                return 1
            seat_id, strategy, token = parts
            bot_assignments[seat_id] = strategy
            tokens[seat_id] = token
    else:
        if len(args.bots) < 2 or len(args.bots) > 6:
            print("--bots needs 2-6 seats", file=sys.stderr)
            return 1
        player_ids = [f"p{i}" for i in range(len(args.bots))]
        bot_assignments = {
            pid: strategy
            for pid, strategy in zip(player_ids, args.bots)
            if strategy != "human"
        }

    for strategy in bot_assignments.values():
        if strategy not in STRATEGIES:
            print(f"Unknown strategy '{strategy}'", file=sys.stderr)
            return 1

    with httpx.Client(base_url=args.url) as client:
        if attaching:
            game_id = args.game_id
            print(f"Attaching to game {game_id}, driving: {bot_assignments}")
        else:
            response = client.post("/games", json={"player_ids": player_ids})
            response.raise_for_status()
            body = response.json()
            game_id = body["game_id"]
            tokens = body["tokens"]
            print(f"Game {game_id} started: {dict(zip(player_ids, args.bots))}")

        def on_turn(state: dict, action: dict) -> None:
            card_name = CardType(action["card_in_hand"]).display_name
            target = f" -> {action['target_player']}" if action.get("target_player") else ""
            print(f"[round {state['round']}] {action['player_id']} played {card_name}{target}")

        winner = drive_game(
            client,
            game_id,
            bot_assignments,
            tokens,
            poll_interval=args.interval,
            on_turn=on_turn,
        )
        print(f"Winner: {winner}")

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "test":
        return _run_test(args)
    if args.command == "serve":
        return _run_serve(args)
    if args.command == "watch":
        return _run_watch(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
