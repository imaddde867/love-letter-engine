"""Engine for Love Letter game management."""

from __future__ import annotations

import random
import uuid
from typing import Optional

from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.player import Player
from love_letter.models.state import GameState


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
            ValueError: If the action is invalid.
        """
        state = self.get_state(game_id, player_id)

        # Validate action
        self._validate_action(state, player_id, action)

        # Execute the action
        state = self._resolve_action(state, player_id, action)

        return state

    def _validate_action(self, state: GameState, player_id: str, action: Action) -> None:
        """Validate an action against the current game state.

        Args:
            state: The current game state.
            player_id: The ID of the player taking the action.
            action: The action to validate.

        Raises:
            ValueError: If the action is invalid, with details in the message.
        """
        player = state.players[player_id]

        # Check player is active
        if not player.is_active:
            raise ValueError(f"Player '{player_id}' is eliminated and cannot act")

        # Check card_in_hand matches player's hand
        if action.card_in_hand != player.hand_card:
            raise ValueError(
                f"Player '{player_id}' must play their hand card "
                f"{player.hand_card}, not {action.card_in_hand}"
            )

        # Check other_card is the remaining card
        # (Player has two cards after drawing: the one they played and the one they keep)
        # This validation happens after the draw step in the engine flow

        # Check target_player exists and is active (for targeting cards)
        if action.target_player:
            if action.target_player not in state.players:
                raise ValueError(f"Target player '{action.target_player}' not found")
            if not state.players[action.target_player].is_active:
                raise ValueError(
                    f"Target player '{action.target_player}' is eliminated"
                )

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
        player.hand_card = action.other_card  # Keep this card
        state.played_cards.append(
            {"player_id": player_id, "card": action.card_in_hand}
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
        """Apply the effect of a played card.

        Args:
            state: The current game state.
            player_id: The ID of the player who played the card.
            action: The action containing the card and any targets/guesses.

        Returns:
            The updated GameState (may have eliminated players).
        """
        card = action.card_in_hand

        # Guard: target + guess
        if card == CardType.GUARD:
            return self._resolve_guard(state, player_id, action)

        # Priest: reveal target's hand
        if card == CardType.PRIEST:
            return self._resolve_priest(state, player_id, action)

        # Baron: compare hands, lower eliminated
        if card == CardType.BARON:
            return self._resolve_baron(state, player_id, action)

        # Handmaid: self-protection (no immediate effect on state)
        if card == CardType.HANDMAID:
            return state

        # Prince: target discards and redraws
        if card == CardType.PRINCE:
            return self._resolve_prince(state, player_id, action)

        # Chancellor: draw 2, keep 1, return 2 to bottom
        if card == CardType.CHANCELLOR:
            return self._resolve_chancellor(state, player_id, action)

        # King: swap hands with target
        if card == CardType.KING:
            return self._resolve_king(state, player_id, action)

        # Countess: no effect (but may force discard if holding King/Prince)
        if card == CardType.COUNTESS:
            return state

        # Princess: discard = elimination
        if card == CardType.PRINCESS:
            player = state.players[player_id]
            player.eliminate()
            return state

        # Spy: no immediate effect
        if card == CardType.SPY:
            return state

        return state

    def _resolve_guard(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve Guard effect: guess target's card."""
        target_id = action.target_player
        guess = action.guess
        if not target_id or not guess:
            raise ValueError("Guard requires target_player and guess")

        # Check if target is protected by Handmaid
        # (Handmaid protection lasts until the start of their next turn)
        # For simplicity, we'll check if the target has Handmaid in hand
        # Actually, Handmaid protection is a state flag, not a card in hand
        # We'll track this in the Player model later

        target = state.players[target_id]
        if target.hand_card == guess:
            target.eliminate()

        return state

    def _resolve_priest(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve Priest effect: reveal target's hand (no state change)."""
        # Priest reveals the target's hand card to the actor
        # This is information only, no state changes needed for engine
        return state

    def _resolve_baron(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve Baron effect: compare hands, lower eliminated."""
        target_id = action.target_player
        if not target_id:
            raise ValueError("Baron requires target_player")

        player = state.players[player_id]
        target = state.players[target_id]

        player_value = player.hand_card.value
        target_value = target.hand_card.value

        if player_value < target_value:
            player.eliminate()
        elif target_value < player_value:
            target.eliminate()
        # Tie: nothing happens

        return state

    def _resolve_prince(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve Prince effect: target discards and redraws."""
        target_id = action.target_player
        if not target_id:
            raise ValueError("Prince requires target_player")

        target = state.players[target_id]

        # Discard target's hand
        discarded_card = target.hand_card
        target.hand_card = None

        # If they discarded the Princess, they are eliminated and don't redraw
        if discarded_card == CardType.PRINCESS:
            target.eliminate()
            return state

        # Redraw from deck or facedown
        if state.deck:
            target.hand_card = state.deck.pop(0)
        elif state.facedown_card is not None:
            target.hand_card = state.facedown_card
            state.facedown_card = None

        return state

    def _resolve_chancellor(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve Chancellor effect: draw 2, keep 1, return 2 to bottom."""
        player = state.players[player_id]

        # Draw 2 cards (or fewer if deck is short)
        drawn: list[CardType] = []
        for _ in range(2):
            if state.deck:
                drawn.append(state.deck.pop(0))
            elif state.facedown_card is not None:
                drawn.append(state.facedown_card)
                state.facedown_card = None
                break

        # Player has 3 cards now: original hand + 2 drawn
        # They keep one and return the other two to the bottom
        # For simplicity, we'll return them in the order they were drawn
        cards_to_return = [c for c in drawn if c != action.other_card]
        # Actually, the player chooses which to keep. The action's other_card is what they keep.
        # So we return the rest.
        for card in cards_to_return:
            state.deck.insert(0, card)  # Bottom of deck

        player.hand_card = action.other_card
        return state

    def _resolve_king(
        self, state: GameState, player_id: str, action: Action
    ) -> GameState:
        """Resolve King effect: swap hands with target."""
        target_id = action.target_player
        if not target_id:
            raise ValueError("King requires target_player")

        player = state.players[player_id]
        target = state.players[target_id]

        # Swap hands
        player.hand_card, target.hand_card = target.hand_card, player.hand_card

        return state

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
