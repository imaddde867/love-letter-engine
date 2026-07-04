# Love Letter Game Context

A fast deduction card game for 2–6 players where suitors try to deliver letters to the Princess. Players draw one card, play one card, and use character abilities to eliminate opponents or survive until the deck runs out. First to reach the required favor tokens wins.

## Language

**Game**:
A complete instance of Love Letter with all its state (deck, players, round tracking).
_Avoid_: Match, session, lobby

**Round**:
A single deal where cards are drawn from a shuffled deck until it runs out or only one player remains. Each round awards one favor token to the winner(s).
_Avoid_: Hand, inning, period

**Favor Token**:
A progress marker. Players accumulate favor tokens across rounds; first to reach the threshold wins the game. Threshold depends on player count (2 players: 6, 3: 5, 4: 4, 5–6: 3).
_Avoid_: Point, score, token

**Card**:
A game piece with a value (0–9) and a specific effect. Each card has a fixed count in the deck (e.g., Guard: 6, Princess: 1). Cards exist in one of three places: a player's hand (hidden), on the table (played faceup), or in the deck (facedown).
_Avoid_: Card instance, card object, character, piece

**Player**:
A participant in the game, identified by a unique ID. Players have a state (active/inactive for the current round) and a hidden hand card.
_Avoid_: User, bot, contestant, participant

**Action**:
A player's turn decision: draw a card, play a card (with optional target and guess), or end the round. Actions are validated before execution.
_Avoid_: Move, play, command

**Effect**:
The resolution logic for a played card. Each card has its own effect (e.g., Guard checks a guess, Priest reveals a hand, Baron compares values). Effects may eliminate players, reveal information, or modify hands.
_Avoid_: Ability, skill, power, spell

**Hand**:
The single hidden card a player is currently holding. At the start of a turn, after drawing, a player holds two cards temporarily and must choose one to play, leaving one card as their hand.
_Avoid_: Hand card, held card, two cards

**Deck**:
The facedown pile of remaining character cards. Cards are drawn from the top. When empty, the round ends.
_Avoid_: Deck pile, card pool

**Played Card**:
A card that has been played faceup on the table. Played cards are visible to all players and track who played them and any targets.
_Avoid_: Discard, table card, public card

**Elimination**:
When a player is removed from the current round due to a card effect (Guard guess, Baron comparison, Prince discard, Princess discard). Eliminated players cannot be targeted and skip future turns until the next round.
_Avoid_: Out, removed, knocked out

**Deduction**:
The process of inferring other players' hidden cards from played cards, effect outcomes, and game state. The game is small enough that memory and tracking matter.
_Avoid_: Guessing, estimating

**Target**:
The player chosen by a card effect (Guard, Priest, Baron, King). Cannot be an eliminated player. If all possible targets are protected by Handmaid, the effect has no impact.
_Avoid_: Victim, choice, selected player

**Guess**:
The character name provided by a Guard player. If the target has that card, they are eliminated.
_Avoid_: Prediction, call

**Protection**:
The defensive state granted by Handmaid. Protected players cannot be chosen as targets by other card effects until the start of their next turn.
_Avoid_: Shield, immunity, bubble
