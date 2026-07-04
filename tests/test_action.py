"""Tests for the Action model."""


def test_create_action_with_required_fields():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
    )
    assert action.action_type == "play_card"
    assert action.card_in_hand == CardType.GUARD
    assert action.other_card == CardType.PRIEST


def test_action_target_player_defaults_to_none():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.HANDMAID,
        other_card=CardType.BARON,
    )
    assert action.target_player is None


def test_action_guess_defaults_to_none():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
    )
    assert action.guess is None


def test_action_with_target_and_guess():
    from love_letter.models.action import Action
    from love_letter.models.card import CardType

    action = Action(
        action_type="play_card",
        card_in_hand=CardType.GUARD,
        other_card=CardType.PRIEST,
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
    )
    assert action.other_card == CardType.COUNTESS
