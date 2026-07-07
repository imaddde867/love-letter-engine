"""Example bot implementations for Love Letter simulation.

Three tiers of bots with increasing sophistication:

- ``RandomBot`` — picks any legal action uniformly at random.
- ``GreedyBot`` — prefers high-value cards and guards against high-value targets.
- ``SpyBot`` — prioritizes Spy information gathering and guess strategy.
"""

from __future__ import annotations

import random

from love_letter.bots import Player
from love_letter.engine.legal_actions import available_actions
from love_letter.models.action import Action
from love_letter.models.card import CardType
from love_letter.models.state import GameState


class RandomBot(Player):
    """Pick any legal action uniformly at random."""

    def choose_action(self, state: GameState) -> Action:
        actions = available_actions(state, self._player_id)
        if not actions:
            raise RuntimeError(f"No legal actions for {self._player_id}")
        return random.choice(actions)

    def set_player_id(self, player_id: str) -> None:
        self._player_id = player_id


class GreedyBot(Player):
    """Prefer high-value cards. Guard against high-value targets when possible."""

    def choose_action(self, state: GameState) -> Action:
        actions = available_actions(state, self._player_id)
        if not actions:
            raise RuntimeError(f"No legal actions for {self._player_id}")

        # Score each action
        scored: list[tuple[int, Action]] = []
        for action in actions:
            score = self._score_action(action, state)
            scored.append((score, action))

        scored.sort(key=lambda x: x[0], reverse=True)
        # Pick from top-scoring actions (tie-break random)
        top_score = scored[0][0]
        top_actions = [a for s, a in scored if s == top_score]
        return random.choice(top_actions)

    def _score_action(self, action: Action, state: GameState) -> int:
        score = 0
        card = action.card_in_hand

        # Prefer playing higher-value cards
        score += card.value * 2

        # Guard: prefer guessing high-value cards against targets likely to hold them
        if card == CardType.GUARD and action.guess is not None:
            score += action.guess.value

        # Prince: prefer targeting players with high-value cards
        if card == CardType.PRINCE and action.target_player:
            target = state.players.get(action.target_player)
            if target and target.hand_card:
                score += target.hand_card.value

        # Baron: prefer targeting players with low-value cards (we eliminate them)
        if card == CardType.BARON and action.target_player:
            target = state.players.get(action.target_player)
            if target and target.hand_card:
                score -= target.hand_card.value  # Lower is better to eliminate

        # Princess: avoid unless forced
        if card == CardType.PRINCESS:
            score -= 100

        return score

    def set_player_id(self, player_id: str) -> None:
        self._player_id = player_id


class SpyBot(Player):
    """Prioritize Spy information gathering, then greedy play."""

    def choose_action(self, state: GameState) -> Action:
        actions = available_actions(state, self._player_id)
        if not actions:
            raise RuntimeError(f"No legal actions for {self._player_id}")

        # Check if we have a Spy and haven't played it this round
        player = state.players[self._player_id]
        has_spy = player.hand_card == CardType.SPY and CardType.SPY not in player.cards_played

        if has_spy:
            # Prioritize playing Spy
            spy_actions = [a for a in actions if a.card_in_hand == CardType.SPY]
            if spy_actions:
                return random.choice(spy_actions)

        # Otherwise play greedy
        greedy = GreedyBot()
        greedy.set_player_id(self._player_id)
        action = greedy.choose_action(state)
        return action

    def set_player_id(self, player_id: str) -> None:
        self._player_id = player_id
