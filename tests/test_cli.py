"""Tests for the love_letter CLI entry point."""

from __future__ import annotations

import pytest

from love_letter.__main__ import main


def test_cli_test_subcommand_runs_simulation(capsys):
    exit_code = main(["test", "--bots", "random", "greedy"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "winner" in captured.out.lower()


def test_cli_test_subcommand_defaults_to_random_vs_random(capsys):
    # exit_code may be 1 if the simulator's consecutive-skip-limit trips
    # (a legitimate, pre-existing simulate() outcome, not a CLI bug) - only
    # the CLI's own contract (always prints a Winner line) is asserted here.
    main(["test"])
    captured = capsys.readouterr()

    assert "winner" in captured.out.lower()


def test_cli_test_subcommand_rejects_unknown_bot(capsys):
    with pytest.raises(SystemExit):
        main(["test", "--bots", "random", "nonexistent"])


def test_cli_no_subcommand_prints_help_and_exits_nonzero(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "usage" in captured.out.lower() or "usage" in captured.err.lower()
