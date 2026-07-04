"""Validation error types for Love Letter engine."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
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

    if action.action_type != "play_card":
        violations.append(Violation(
            field="action_type",
            message=f"Unsupported action type: {action.action_type}",
            code="UNSUPPORTED_ACTION_TYPE",
        ))

    if action.player_id != player_id:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} is not the actor",
            code="PLAYER_MISMATCH",
        ))

    if player_id not in state.players:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} not found in game",
            code="PLAYER_NOT_FOUND",
        ))
        return violations

    actor = state.players[player_id]
    if not actor.is_active:
        violations.append(Violation(
            field="player_id",
            message=f"Player {player_id} is eliminated",
            code="PLAYER_NOT_ACTIVE",
        ))

    active_player_ids = [
        pid for pid, player in state.players.items()
        if player.is_active
    ]
    if active_player_ids:
        expected_player = active_player_ids[
            state.current_player_index % len(active_player_ids)
        ]
        if player_id != expected_player:
            violations.append(Violation(
                field="player_id",
                message=f"It is {expected_player}'s turn, not {player_id}'s",
                code="NOT_CURRENT_PLAYER",
            ))

    if actor.hand_card is None:
        violations.append(Violation(
            field="card_in_hand",
            message=f"Player {player_id} has no card in hand",
            code="NO_CARD_IN_HAND",
        ))
    elif not state.deck:
        violations.append(Violation(
            field=None,
            message="Cannot take a turn when the deck is empty",
            code="ROUND_OVER",
        ))
    else:
        available_cards = Counter([actor.hand_card, state.deck[0]])
        requested_cards = Counter([action.card_in_hand, action.other_card])
        if requested_cards != available_cards:
            violations.append(Violation(
                field="card_in_hand",
                message="card_in_hand and other_card must match the player's hand plus drawn card",
                code="CARDS_NOT_AVAILABLE",
            ))

        if (
            CardType.COUNTESS in available_cards
            and any(card in available_cards for card in (CardType.KING, CardType.PRINCE))
            and action.card_in_hand != CardType.COUNTESS
        ):
            violations.append(Violation(
                field="card_in_hand",
                message="Countess must be played when held with King or Prince",
                code="COUNTESS_REQUIRED",
            ))

    target_required_cards = {
        CardType.GUARD,
        CardType.PRIEST,
        CardType.BARON,
        CardType.KING,
    }
    if action.card_in_hand in target_required_cards:
        if not action.target_player:
            violations.append(Violation(
                field="target_player",
                message=f"{action.card_in_hand.display_name} requires a target_player",
                code="MISSING_TARGET",
            ))
        elif action.target_player == player_id:
            violations.append(Violation(
                field="target_player",
                message=f"{action.card_in_hand.display_name} must target another player",
                code="INVALID_TARGET_SELF",
            ))

    if action.card_in_hand == CardType.PRINCE and not action.target_player:
        violations.append(Violation(
            field="target_player",
            message="Prince requires a target_player",
            code="MISSING_TARGET",
        ))

    if action.target_player:
        target = state.players.get(action.target_player)
        if target is None:
            violations.append(Violation(
                field="target_player",
                message=f"Target player {action.target_player} not found",
                code="TARGET_NOT_FOUND",
            ))
        elif not target.is_active:
            violations.append(Violation(
                field="target_player",
                message=f"Target player {action.target_player} is eliminated",
                code="TARGET_NOT_ACTIVE",
            ))

    if action.card_in_hand == CardType.GUARD:
        if action.guess is None:
            violations.append(Violation(
                field="guess",
                message="Guard requires a guess",
                code="MISSING_GUESS",
            ))
        elif action.guess == CardType.GUARD:
            violations.append(Violation(
                field="guess",
                message="Guard cannot guess Guard",
                code="INVALID_GUARD_GUESS",
            ))

    return violations
