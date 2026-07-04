"""Tests for the engine error types."""

from love_letter.engine.errors import (
    GameOverError,
    InvalidActionError,
    PlayerNotActiveError,
    Violation,
)


def test_invalid_action_error_with_violations():
    """InvalidActionError contains a list of violations."""
    violations = [
        Violation(field="target_player", message="Target required", code="MISSING_TARGET"),
        Violation(field="guess", message="Guess required", code="MISSING_GUESS"),
    ]

    error = InvalidActionError(violations)
    assert len(error.violations) == 2
    assert "Target required" in str(error)


def test_invalid_action_error_empty_violations():
    """InvalidActionError with no violations has a default message."""
    error = InvalidActionError()
    assert len(error.violations) == 0
    assert "unknown validation error" in str(error)


def test_invalid_action_error_add_violation():
    """InvalidActionError can have violations added."""
    error = InvalidActionError()
    error.add_violation(
        Violation(field="target_player", message="Target required", code="MISSING_TARGET")
    )
    assert len(error.violations) == 1


def test_game_over_error_message():
    """GameOverError includes the game ID."""
    error = GameOverError("game-123")
    assert error.game_id == "game-123"
    assert "game-123" in str(error)


def test_player_not_active_error_message():
    """PlayerNotActiveError includes the player ID."""
    error = PlayerNotActiveError("alice")
    assert error.player_id == "alice"
    assert "alice" in str(error)


def test_violation_dataclass():
    """Violation is a dataclass with field, message, and code."""
    v = Violation(field="target_player", message="Required", code="REQUIRED")
    assert v.field == "target_player"
    assert v.message == "Required"
    assert v.code == "REQUIRED"
