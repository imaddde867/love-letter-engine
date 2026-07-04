# Property-Based and Unit Testing Strategy

The test suite uses property-based testing (via hypothesis) for game rules combined with unit tests for individual card effects.

Property tests assert invariants like "a round always ends when the deck is empty or one player remains" and "after any valid move, the game state is still valid." Unit tests verify each card effect in isolation.

Example-based testing alone was considered but rejected because Love Letter has subtle interactions between cards that are hard to cover manually. Property tests catch edge cases automatically and make refactoring safer.
