"""Tests for the Card model."""


def test_card_enum_has_all_ten_types():
    from love_letter.models.card import CardType

    assert len(CardType) == 10


def test_card_values_are_sequential_zero_to_nine():
    from love_letter.models.card import CardType

    values = [c.value for c in CardType]
    assert values == list(range(10))


def test_card_counts_sum_to_twenty_one():
    from love_letter.models.card import CardType

    total = sum(c.count for c in CardType)
    assert total == 21


def test_guard_has_correct_metadata():
    from love_letter.models.card import CardType

    g = CardType.GUARD
    assert g.display_name == "Guard"
    assert g.value == 1
    assert g.count == 6


def test_princess_has_correct_metadata():
    from love_letter.models.card import CardType

    p = CardType.PRINCESS
    assert p.display_name == "Princess"
    assert p.value == 9
    assert p.count == 1


def test_card_count_is_positive_for_all_types():
    from love_letter.models.card import CardType

    for card in CardType:
        assert card.count > 0

