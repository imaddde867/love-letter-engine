"""Tests for the Player model."""


def test_create_player_with_id():
    from love_letter.models.card import CardType
    from love_letter.models.player import Player

    p = Player(id="alice")
    assert p.id == "alice"


def test_player_defaults_active_and_zero_favor():
    from love_letter.models.player import Player

    p = Player(id="bob")
    assert p.is_active is True
    assert p.favor_tokens == 0


def test_player_starts_without_hand_card():
    from love_letter.models.player import Player

    p = Player(id="carol")
    assert p.hand_card is None


def test_set_hand_card():
    from love_letter.models.card import CardType
    from love_letter.models.player import Player

    p = Player(id="dave")
    p.hand_card = CardType.GUARD
    assert p.hand_card == CardType.GUARD


def test_eliminate_player():
    from love_letter.models.player import Player

    p = Player(id="eve")
    assert p.is_active is True
    p.eliminate()
    assert p.is_active is False


def test_add_favor_token():
    from love_letter.models.player import Player

    p = Player(id="frank")
    p.add_favor()
    p.add_favor()
    assert p.favor_tokens == 2


def test_cards_played_tracks_placed_cards():
    from love_letter.models.card import CardType
    from love_letter.models.player import Player

    p = Player(id="grace")
    p.cards_played.append(CardType.PRIEST)
    assert CardType.PRIEST in p.cards_played
