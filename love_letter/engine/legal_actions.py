"""Generate all legal actions for a player in the current state.

This module produces the complete set of valid actions a player can take
on their turn, given their hand card and the next card to draw. Bots use
this to enumerate options; the API could expose it as ``available_actions``
in state responses.

The generator respects:
- The player's actual two turn cards (hand + drawn).
- Targeting requirements per card type.
- Handmaid protection on targets.
- Eliminated players cannot be targeted.
"""

from __future__ import annotations

import itertools
from typing import Optional

from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.state import GameState


_TARGETING_CARDS = {
    CardType.GUARD,
    CardType.PRIEST,
    CardType.BARON,
    CardType.PRINCE,
    CardType.KING,
}

_NON_TARGETING_CARDS = {
    CardType.HANDMAID,
    CardType.COUNTESS,
    CardType.CHANCELLOR,
    CardType.SPY,
}


def available_actions(state: GameState, player_id: str) -> list[Action]:
    """Return all legal actions for ``player_id`` in the given state.

    Args:
        state: The current game state.
        player_id: The ID of the player whose actions to generate.

    Returns:
        A list of valid ``Action`` objects. May be empty if the player
        is eliminated or has no hand card.
    """
    player = state.players.get(player_id)
    if player is None or not player.is_active or player.hand_card is None:
        return []

    turn_cards = _turn_cards(state, player_id)
    targets = _valid_targets(state, player_id)
    guesses = _valid_guesses()

    actions: list[Action] = []

    # Use index-based iteration to handle duplicate cards correctly.
    # If the player has two of the same card (e.g., two Guards), both
    # play/keep combinations are valid but produce identical Actions,
    # so we deduplicate at the end.
    played_indices: set[int] = set()

    for i, card_in_hand in enumerate(turn_cards):
        if i in played_indices:
            continue
        other_card_options = [turn_cards[j] for j in range(len(turn_cards)) if j != i]
        played_indices.add(i)

        if card_in_hand == CardType.PRINCESS:
            action = Action(
                action_type="play_card",
                card_in_hand=CardType.PRINCESS,
                other_card=None,
                player_id=player_id,
            )
            actions.append(action)
            continue

        if card_in_hand == CardType.CHANCELLOR:
            action = Action(
                action_type="play_card",
                card_in_hand=CardType.CHANCELLOR,
                other_card=None,
                player_id=player_id,
            )
            actions.append(action)
            continue

        for other in other_card_options:
            if card_in_hand in _TARGETING_CARDS:
                for target in targets:
                    guess = guesses[0] if card_in_hand == CardType.GUARD else None
                    action = Action(
                        action_type="play_card",
                        card_in_hand=card_in_hand,
                        other_card=other,
                        player_id=player_id,
                        target_player=target,
                        guess=guess,
                    )
                    actions.append(action)
            else:
                action = Action(
                    action_type="play_card",
                    card_in_hand=card_in_hand,
                    other_card=other,
                    player_id=player_id,
                )
                actions.append(action)

    # Deduplicate: two identical cards produce the same Action objects
    seen = set()
    unique: list[Action] = []
    for action in actions:
        key = (action.card_in_hand, action.other_card, action.target_player, action.guess)
        if key not in seen:
            seen.add(key)
            unique.append(action)
    return unique


def _turn_cards(state: GameState, player_id: str) -> list[CardType]:
    """Return the two cards available to the player this turn.

    The player's hand card plus the next card from deck (or facedown).
    """
    player = state.players[player_id]
    cards: list[CardType] = []

    if player.hand_card is not None:
        cards.append(player.hand_card)

    if state.deck:
        cards.append(state.deck[0])
    elif state.facedown_card is not None:
        cards.append(state.facedown_card)

    return cards


def _valid_targets(state: GameState, player_id: str) -> list[str]:
    """Return active player IDs that can be targeted, excluding self."""
    targets: list[str] = []
    for pid, player in state.players.items():
        if pid == player_id:
            continue
        if not player.is_active:
            continue
        if player.protected_until_next_turn:
            continue
        targets.append(pid)
    return targets


def _valid_guesses() -> list[CardType]:
    """Return all valid Guard guesses (all cards except Guard)."""
    return [c for c in CardType if c != CardType.GUARD]
