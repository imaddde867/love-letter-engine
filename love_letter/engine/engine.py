"""Engine for Love Letter game management."""

from __future__ import annotations

import random
import uuid
from typing import Optional

from love_letter.engine.effects.baron import BaronEffect
from love_letter.engine.effects.chancellor import ChancellorEffect
from love_letter.engine.effects.countess import CountessEffect
from love_letter.engine.effects.guard import GuardEffect
from love_letter.engine.effects.handmaid import HandmaidEffect
from love_letter.engine.effects.king import KingEffect
from love_letter.engine.effects.priest import PriestEffect
from love_letter.engine.effects.prince import PrinceEffect
from love_letter.engine.effects.princess import PrincessEffect
from love_letter.engine.effects.spy import SpyEffect
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState

from love_letter.engine.errors import (
    GameOverError,
    InvalidActionError,
    Violation,
    PlayerNotActiveError,
    validate_action,
)


class Engine:
    """Manages multiple concurrent Love Letter games in memory.

    The engine holds game state and provides methods to create games,
    retrieve state, and execute actions.
    """

    # Favor token thresholds based on player count
    FAVOR_THRESHOLDS: dict[int, int] = {
        2: 6,
        3: 5,
        4: 4,
        5: 3,
        6: 3,
    }

    def __init__(self) -> None:
        self._games: dict[str, GameState] = {}

    def create_game(self, player_ids: list[str]) -> str:
        """Create a new game with the given player IDs.

        Args:
            player_ids: List of unique player identifiers. Must be 2-6 players.

        Returns:
            The game ID for the newly created game.

        Raises:
            ValueError: If player count is outside 2-6 range or IDs are duplicated.
        """
        if len(player_ids) < 2 or len(player_ids) > 6:
            raise ValueError(f"Player count must be 2-6, got {len(player_ids)}")
        if len(set(player_ids)) != len(player_ids):
            raise ValueError("Player IDs must be unique")

        game_id = str(uuid.uuid4())

        # Create players
        players = {pid: Player(id=pid) for pid in player_ids}

        # Build and shuffle deck
        deck: list[CardType] = []
        for card_type in CardType:
            deck.extend([card_type] * card_type.count)
        random.shuffle(deck)

        # Set aside top card facedown
        facedown_card = deck.pop(0) if deck else None

        # Determine favor threshold
        threshold = self.FAVOR_THRESHOLDS[len(player_ids)]

        # Deal one card to each player
        for pid in player_ids:
            if deck:
                players[pid].hand_card = deck.pop(0)

        state = GameState(
            game_id=game_id,
            round=1,
            deck=deck,
            facedown_card=facedown_card,
            players=players,
            current_player_index=0,
            favor_token_threshold=threshold,
        )

        self._games[game_id] = state
        return game_id

    def get_state(self, game_id: str, player_id: str) -> GameState:
        """Get the current game state for a specific player.

        Args:
            game_id: The ID of the game to retrieve.
            player_id: The ID of the player requesting state.

        Returns:
            The GameState object.

        Raises:
            KeyError: If game_id or player_id is not found.
        """
        if game_id not in self._games:
            raise KeyError(f"Game '{game_id}' not found")
        state = self._games[game_id]
        if player_id not in state.players:
            raise KeyError(f"Player '{player_id}' not in game '{game_id}'")
        return state

    def execute_action(self, game_id: str, player_id: str, action: Action) -> GameState:
        """Execute an action for a player in a game.

        Args:
            game_id: The ID of the game.
            player_id: The ID of the player taking the action.
            action: The action to execute.

        Returns:
            The updated GameState.

        Raises:
            KeyError: If game_id or player_id is not found.
            GameOverError: If the game has already ended.
            InvalidActionError: If the action is invalid.
        """
        state = self.get_state(game_id, player_id)

        # Check if game is over before executing
        if self._is_game_over(state):
            raise GameOverError(game_id)

        # Validate action and raise InvalidActionError with violations
        violations = validate_action(action, player_id, state)
        if violations:
            raise InvalidActionError(violations)

        # Execute the action
        state = self._resolve_action(state, player_id, action)

        return state

    def _resolve_action(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve an action and update game state.

        This is the core turn flow: draw, play, resolve effect, check round end.

        Args:
            state: The current game state.
            player_id: The ID of the player taking the action.
            action: The validated action to resolve.

        Returns:
            The updated GameState.
        """
        player = state.players[player_id]

        # Clear Handmaid protection at the start of the player's turn
        if player.protected_until_next_turn:
            player.protected_until_next_turn = False

        expected_cards = [player.hand_card]
        if state.deck:
            expected_cards.append(state.deck[0])
        elif state.facedown_card is not None:
            expected_cards.append(state.facedown_card)

        if action.card_in_hand == CardType.CHANCELLOR:
            if CardType.CHANCELLOR not in expected_cards:
                raise InvalidActionError([
                    Violation(
                        field="card_in_hand",
                        message="Played card must match the player's hand plus drawn card",
                        code="CARD_NOT_AVAILABLE",
                    )
                ])
        else:
            if action.other_card is None:
                # Princess discard: card_in_hand must be one of the available cards
                if action.card_in_hand not in expected_cards:
                    raise InvalidActionError([
                        Violation(
                            field="card_in_hand",
                            message="Played card must be one of the available cards",
                            code="CARD_NOT_AVAILABLE",
                        )
                    ])
            else:
                submitted_cards = [action.card_in_hand, action.other_card]
                if sorted(submitted_cards) != sorted(expected_cards):
                    raise InvalidActionError([
                        Violation(
                            field="card_in_hand",
                            message="Played and kept cards must match the player's hand plus drawn card",
                            code="CARD_NOT_AVAILABLE",
                        )
                    ])

        # Step 1: Draw a card from the deck
        if state.deck:
            drawn_card = state.deck.pop(0)
        elif state.facedown_card is not None:
            # Deck empty, draw from facedown
            drawn_card = state.facedown_card
            state.facedown_card = None
        else:
            # No cards left, round should have ended
            return state

        # Player now has two cards: the drawn one and their current hand
        # They must play one and keep the other
        # The action specifies which is which via card_in_hand (played) and other_card (kept)

        # Step 2: Play the card (remove from hand, add to played)
        if action.card_in_hand == CardType.CHANCELLOR:
            initial_options = expected_cards.copy()
            initial_options.remove(CardType.CHANCELLOR)
            player.hand_card = initial_options[0] if initial_options else None
        elif action.card_in_hand == CardType.PRINCESS and action.other_card is None:
            # Princess discard: player has no hand card after
            player.hand_card = None
        else:
            player.hand_card = action.other_card  # Keep this card
        state.played_cards.append(
            {
                "player_id": player_id,
                "card": action.card_in_hand,
                "target_player": action.target_player,
            }
        )

        # Track cards played by this player (for Spy bonus)
        if action.card_in_hand not in player.cards_played:
            player.cards_played.append(action.card_in_hand)

        # Step 3: Resolve the card effect
        state = self._apply_card_effect(state, player_id, action)

        # Step 4: Check if round should end
        if self._is_round_over(state):
            self._end_round(state)
            return state

        # Step 5: Advance to next player
        active_players = [p for p in state.players.values() if p.is_active]
        if active_players:
            state.current_player_index = (state.current_player_index + 1) % len(
                active_players
            )

        return state

    def _apply_card_effect(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Apply the effect of a played card using strategy pattern.

        Args:
            state: The current game state.
            player_id: The ID of the player who played the card.
            action: The action containing the card and any targets/guesses.

        Returns:
            The updated GameState (may have eliminated players).
        """
        card = action.card_in_hand

        effect_map: dict[CardType, type] = {
            CardType.GUARD: GuardEffect,
            CardType.PRIEST: PriestEffect,
            CardType.BARON: BaronEffect,
            CardType.HANDMAID: HandmaidEffect,
            CardType.PRINCE: PrinceEffect,
            CardType.CHANCELLOR: ChancellorEffect,
            CardType.KING: KingEffect,
            CardType.COUNTESS: CountessEffect,
            CardType.PRINCESS: PrincessEffect,
            CardType.SPY: SpyEffect,
        }

        effect_cls = effect_map.get(card)
        if effect_cls is None:
            raise ValueError(f"Unknown card type: {card}")

        return effect_cls.resolve(state, action)

    def _is_round_over(self, state: GameState) -> bool:
        """Check if the round should end.

        A round ends when:
        1. The deck is empty AND facedown card is None
        2. Only one player remains active

        Args:
            state: The current game state.

        Returns:
            True if the round should end.
        """
        # Check if only one player remains
        active_players = [p for p in state.players.values() if p.is_active]
        if len(active_players) <= 1:
            return True

        # Check if deck is empty
        if state.deck_count == 0 and state.facedown_card is None:
            return True

        return False

    def _end_round(self, state: GameState) -> None:
        """End the current round and award favor tokens.

        Args:
            state: The game state to finalize.
        """
        active_players = [p for p in state.players.values() if p.is_active]

        if not active_players:
            # Should not happen, but handle gracefully
            return

        # Determine round winner(s)
        if len(active_players) == 1:
            # Only one player left, they win
            winners = active_players
        else:
            # Deck ran out, highest card value wins
            max_value = max(p.hand_card.value for p in active_players if p.hand_card)
            winners = [p for p in active_players if p.hand_card and p.hand_card.value == max_value]

        # Award favor tokens to winners
        for winner in winners:
            winner.add_favor()

        # Award Spy bonus: if only one active player played a Spy, give them extra favor
        spy_players = [
            p for p in active_players
            if CardType.SPY in p.cards_played
        ]
        if len(spy_players) == 1:
            spy_players[0].add_favor()

        # Check if any player has reached the threshold
        # (Game over check happens in execute_action after this)

    def _is_game_over(self, state: GameState) -> bool:
        """Check if the game is over (any player reached threshold).

        Args:
            state: The current game state.

        Returns:
            True if the game is over.
        """
        return any(
            p.favor_tokens >= state.favor_token_threshold
            for p in state.players.values()
        )
