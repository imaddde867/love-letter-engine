"""Tests for the engine error types and validate_action()."""

from love_letter.engine.errors import (
    GameOverError,
    InvalidActionError,
    PlayerNotActiveError,
    Violation,
    validate_action,
)
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


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


def _make_state(players: list[str] | None = None) -> GameState:
    """Build a minimal GameState with active players."""
    state = GameState(game_id="g1", round=1)
    for pid in players or ["alice", "bob"]:
        p = Player(id=pid)
        p.hand_card = CardType.HANDMAID
        state.players[pid] = p
    return state


def _make_action(**overrides: object) -> Action:
    """Build a default Action with sensible defaults."""
    base = dict(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        player_id="alice",
        other_card=CardType.HANDMAID,
        target_player="bob",
        guess=CardType.PRIEST,
    )
    base.update(overrides)
    return Action(**base)  # type: ignore[arg-type]


def test_validate_action_guard_missing_target():
    """Guard without target_player returns MISSING_TARGET violation."""
    action = _make_action(card_in_hand=CardType.GUARD, target_player=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_TARGET" in codes


def test_validate_action_priest_missing_target():
    """Priest without target_player returns MISSING_TARGET violation."""
    action = _make_action(card_in_hand=CardType.PRIEST, target_player=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_TARGET" in codes


def test_validate_action_baron_missing_target():
    """Baron without target_player returns MISSING_TARGET violation."""
    action = _make_action(card_in_hand=CardType.BARON, target_player=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_TARGET" in codes


def test_validate_action_king_missing_target():
    """King without target_player returns MISSING_TARGET violation."""
    action = _make_action(card_in_hand=CardType.KING, target_player=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_TARGET" in codes


def test_validate_action_prince_missing_target():
    """Prince without target_player returns MISSING_TARGET violation."""
    action = _make_action(card_in_hand=CardType.PRINCE, target_player=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_TARGET" in codes


def test_validate_action_guard_missing_guess():
    """Guard without guess returns MISSING_GUARD_GUESS violation."""
    action = _make_action(guess=None)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "MISSING_GUARD_GUESS" in codes


def test_validate_action_guard_guesses_guard():
    """Guard guessing Guard returns GUARD_GUESSES_GUARD violation."""
    action = _make_action(guess=CardType.GUARD)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "GUARD_GUESSES_GUARD" in codes


def test_validate_action_target_not_in_game():
    """Target player not in game returns TARGET_NOT_FOUND violation."""
    action = _make_action(target_player="charlie")
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "TARGET_NOT_FOUND" in codes


def test_validate_action_target_eliminated():
    """Target player eliminated returns TARGET_NOT_ACTIVE violation."""
    state = _make_state()
    state.players["bob"].eliminate()
    action = _make_action(target_player="bob")
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "TARGET_NOT_ACTIVE" in codes


def test_validate_action_prince_target_not_in_game():
    """Prince with unknown target returns TARGET_NOT_FOUND violation."""
    action = _make_action(card_in_hand=CardType.PRINCE, target_player="charlie")
    state = _make_state()
    violations = validate_action(action, "alice", state)
    codes = [v.code for v in violations]
    assert "TARGET_NOT_FOUND" in codes


def test_validate_action_non_targeting_card_no_target_required():
    """Non-targeting cards (Chancellor) do not require target_player."""
    action = _make_action(
        card_in_hand=CardType.CHANCELLOR,
        target_player=None,
        other_card=CardType.HANDMAID,
    )
    state = _make_state()
    violations = validate_action(action, "alice", state)
    target_violations = [v for v in violations if v.code == "MISSING_TARGET"]
    assert target_violations == []


def test_validate_action_valid_guard_action():
    """Valid Guard action with correct target and guess produces no violations."""
    action = _make_action(card_in_hand=CardType.GUARD, guess=CardType.PRIEST)
    state = _make_state()
    violations = validate_action(action, "alice", state)
    assert violations == []
