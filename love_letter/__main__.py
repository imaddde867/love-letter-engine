"""CLI entry point for the Love Letter engine.

Provides two subcommands:
- ``test``: run a bot-vs-bot simulation and print the result.
- ``serve``: start the FastAPI HTTP server via uvicorn.
"""

from __future__ import annotations

import argparse
import sys

from love_letter.bots import Player
from love_letter.bots.examples import GreedyBot, RandomBot, SpyBot
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


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "test":
        return _run_test(args)
    if args.command == "serve":
        return _run_serve(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
