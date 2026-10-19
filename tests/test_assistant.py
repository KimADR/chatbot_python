import pytest

from orinasa.assistant import search_cards
from orinasa.knowledge import CARDS


@pytest.mark.parametrize("card", CARDS)
def test_card_search_finds_each_card_by_keyword(card):
    result = search_cards(card["keywords"][0], limit=5)
    assert any(item["id"] == card["id"] for item in result)


@pytest.mark.parametrize("card", CARDS)
def test_card_search_finds_each_card_by_title(card):
    result = search_cards(card["title"], limit=5)
    assert any(item["id"] == card["id"] for item in result)
