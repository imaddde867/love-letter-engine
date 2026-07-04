"""Tests for the Action model."""


def test_create_action_with_required_fields():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
    )
    assert action.action_type == "play_card"
    assert action.card_in_hand == CardType.GUARD
    assert action.other_card == CardType.PRIEST
    assert action.player_id == "alice"


def test_action_target_player_defaults_to_none():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        other_card=CardType.BARON,
        player_id="alice",
    )
    assert action.target_player is None


def test_action_guess_defaults_to_none():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
    )
    assert action.guess is None


def test_action_with_target_and_guess():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
        player_id="alice",
        target_player="bob",
        guess=CardType.BARON,
    )
    assert action.target_player == "bob"
    assert action.guess == CardType.BARON


def test_action_preserves_other_card_for_non_targeting_cards():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        other_card=CardType.COUNTESS,
        player_id="alice",
    )
    assert action.other_card == CardType.COUNTESS
