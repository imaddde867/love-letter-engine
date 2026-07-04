# REST API with Reactive Game Flow

The HTTP API uses REST endpoints with a purely reactive game flow. The engine waits for each action and does not enforce timers or auto-advance turns.

This was chosen over WebSocket/real-time approaches because it's simpler to debug, works with any HTTP client (including curl), and makes testing trivial. Timers and auto-forfeit can be added later as an optional feature.

The API contract is: "give me an action, I give you back the new state." Each request is self-contained and includes the player ID.
