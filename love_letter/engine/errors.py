"""Validation error types for Love Letter engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Violation:
    """A single validation violation.

    Attributes:
        field: The field that failed validation (or None for global errors).
        message: Human-readable description of the violation.
        code: Machine-readable error code for programmatic handling.
    """

    field: str | None
    message: str
    code: str


class InvalidActionError(Exception):
    """Raised when an action fails validation.

    Contains a list of Violation objects describing all issues found.
    This is the standard error type for the engine's validation layer.

    Attributes:
        violations: List of all validation failures found in the action.
    """

    def __init__(self, violations: list[Violation] | None = None) -> None:
        self.violations: list[Violation] = violations or []
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        """Format violations into a human-readable string."""
        if not self.violations:
            return "Invalid action: unknown validation error"

        fields = {v.field for v in self.violations if v.field}
        if len(fields) == 1:
            return f"Invalid action on field '{fields.pop()}': {self.violations[0].message}"

        messages = "; ".join(v.message for v in self.violations)
        return f"Invalid action: {messages}"

    def add_violation(self, violation: Violation) -> None:
        """Add a violation to this error.

        Args:
            violation: The violation to add.
        """
        self.violations.append(violation)

    @classmethod
    def from_violations(cls, violations: list[Violation]) -> "InvalidActionError":
        """Create an InvalidActionError from a list of violations.

        Args:
            violations: List of Violation objects.

        Returns:
            A new InvalidActionError instance.
        """
        error = cls(violations)
        return error


class GameNotFoundError(Exception):
    """Raised when a game ID is not found."""

    def __init__(self, game_id: str) -> None:
        self.game_id = game_id
        super().__init__(f"Game not found: {game_id}")


class PlayerNotFoundError(Exception):
    """Raised when a player ID is not found in a game."""

    def __init__(self, game_id: str, player_id: str) -> None:
        self.game_id = game_id
        self.player_id = player_id
        super().__init__(f"Player not found in game: player={player_id}, game={game_id}")


class PlayerNotActiveError(Exception):
    """Raised when an action is attempted by an inactive player."""

    def __init__(self, player_id: str) -> None:
        self.player_id = player_id
        super().__init__(f"Player is not active: {player_id}")


class GameOverError(Exception):
    """Raised when an action is attempted on a game that has ended."""

    def __init__(self, game_id: str) -> None:
        self.game_id = game_id
        super().__init__(f"Game is over: {game_id}")


def validate_action(action: Any, player_id: str, state: Any) -> list[Violation]:
    """Validate an action against the current game state.

    This is a helper function that checks common validation rules and returns
    a list of violations. Empty list means the action is valid.

    Args:
        action: The action to validate.
        player_id: The ID of the player taking the action.
        state: The current game state.

    Returns:
        List of Violation objects. Empty if valid.
    """
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    violations: list[Violation] = []

    # Check action type
    if not isinstance(action, Action):
        violations.append(Violation(
            field="action_type",
            message="Action must be an instance of Action",
            code="INVALID_ACTION_TYPE",
        ))
        return violations

    # Check player is active
    if action.player_id != player_id:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} is not the actor",
            code="PLAYER_MISMATCH",
        ))

    # Check player exists and is active in state
    if player_id not in state.players:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} not found in game",
            code="PLAYER_NOT_FOUND",
        ))
    elif not state.players[player_id].is_active:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} is eliminated",
            code="PLAYER_NOT_ACTIVE",
        ))

    # Princess must be discarded with other_card=None
    if action.card_in_hand == CardType.PRINCESS and action.other_card is not None:
        violations.append(Violation(
            field="other_card",
            message="Princess discard requires other_card to be None",
            code="INVALID_OTHER_CARD",
        ))

    # Targeting cards require a valid target_player
    _validate_target(action, state, violations)

    # Guard-specific: guess required and cannot be GUARD
    if action.card_in_hand == CardType.GUARD:
        if action.guess is None:
            violations.append(Violation(
                field="guess",
                message="Guard requires a guess (card type)",
                code="MISSING_GUARD_GUESS",
            ))
        elif action.guess == CardType.GUARD:
            violations.append(Violation(
                field="guess",
                message="Cannot guess Guard",
                code="GUARD_GUESSES_GUARD",
            ))

    return violations


def _validate_target(action: Any, state: Any, violations: list[Violation]) -> None:
    """Validate target_player for cards that require a target.

    Targeting cards: Guard, Priest, Baron, King, Prince.

    Args:
        action: The action to validate.
        state: The current game state.
        violations: Mutable list of Violations to append to.
    """
    from love_letter.models.card import CardType

    targeting_cards = {
        CardType.GUARD,
        CardType.PRIEST,
        CardType.BARON,
        CardType.PRINCE,
        CardType.KING,
    }

    if action.card_in_hand not in targeting_cards:
        return

    target_id = action.target_player

    # Missing or empty target
    if not target_id:
        violations.append(Violation(
            field="target_player",
            message=f"{action.card_in_hand.name} requires a target_player",
            code="MISSING_TARGET",
        ))
        return

    # Target player does not exist in game
    if target_id not in state.players:
        violations.append(Violation(
            field="target_player",
            message=f"Target player '{target_id}' not found in game",
            code="TARGET_NOT_FOUND",
        ))
        return

    # Target player is eliminated
    target = state.players[target_id]
    if not target.is_active:
        violations.append(Violation(
            field="target_player",
            message=f"Target player '{target_id}' is eliminated",
            code="TARGET_NOT_ACTIVE",
        ))
