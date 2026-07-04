"""Action model for Love Letter."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict

from love_letter.models.card import CardType


class Action(BaseModel):
    """A player's turn decision.

    Pydantic BaseModel so it can be parsed directly from JSON request bodies
    in the API layer while remaining fully compatible with the engine.

    Attributes:
        action_type: The type of action (currently always "play_card").
        card_in_hand: The card being played faceup.
        other_card: The card kept in hand after the turn.
        player_id: The ID of the player taking the action.
        target_player: Optional target player ID (for Guard, Priest, Baron, King).
        guess: Optional guessed card type (for Guard).
    """

    model_config = ConfigDict(from_attributes=True)

    action_type: str
    card_in_hand: CardType
    other_card: CardType
    player_id: str
    target_player: Optional[str] = None
    guess: Optional[CardType] = None
