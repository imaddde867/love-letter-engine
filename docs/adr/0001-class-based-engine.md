# Class-Based Engine Architecture

The engine is implemented as a class with encapsulated game state, not as a collection of pure functions.

The engine holds multiple games in memory and exposes methods like `create_game()`, `execute_action()`, and `get_state()`. This allows stateful management of concurrent games and makes it easy to add persistence later without changing the public API.

Functional alternatives (pure `play_move(state, action) -> state`) were considered but rejected because they don't scale well to multiple concurrent games and make it harder to add features like game history or state snapshots.
