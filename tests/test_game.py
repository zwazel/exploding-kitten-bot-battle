import copy

from card import CardCounts, CardType
from game_handling.game import Game

from tests.test_bots import (
    CheaterPlayBot,
    CheaterDefuseBot,
    SkipBot,
    SeeFutureBot,
)


def create_game(bot):
    card_counts = CardCounts(
        EXPLODING_KITTEN=0,
        DEFUSE=1,
        SKIP=0,
        SEE_THE_FUTURE=0,
        NORMAL=6,
    )
    game = Game(testing=True, bots=[bot], card_counts=copy.deepcopy(card_counts))
    game.setup()
    return game


def test_bot_cannot_play_unregistered_card():
    bot = CheaterPlayBot()
    game = create_game(bot)
    # ensure deck has a known card to draw
    game.deck.cards = [game.deck.create_card(CardType.NORMAL)]
    game.game_state.cards_left_to_draw = game.deck.cards_left()
    discard_before = len(game.deck.discard_pile)

    game.take_turn(bot)

    assert game.deck.cards_left() == 0
    assert len(game.deck.discard_pile) == discard_before
    assert any(c.card_type == CardType.NORMAL for c in bot.hand)


def test_fake_defuse_does_not_prevent_explosion():
    bot = CheaterDefuseBot()
    game = create_game(bot)
    # force next draw to be an exploding kitten
    game.deck.cards = [game.deck.create_card(CardType.EXPLODING_KITTEN)]
    game.game_state.cards_left_to_draw = game.deck.cards_left()

    game.take_turn(bot)

    assert not bot.alive
    assert any(c.card_type == CardType.EXPLODING_KITTEN for c in game.deck.discard_pile)


def test_skip_card_ends_turn_without_drawing():
    bot = SkipBot()
    game = create_game(bot)
    skip_card = game.deck.create_card(CardType.SKIP)
    bot.add_card(skip_card)
    starting_cards = game.deck.cards_left()

    game.take_turn(bot)

    assert game.deck.cards_left() == starting_cards
    assert skip_card not in bot.hand
    assert skip_card in game.deck.discard_pile


def test_see_the_future_peeks_top_three():
    bot = SeeFutureBot()
    game = create_game(bot)
    first = game.deck.create_card(CardType.NORMAL)
    second = game.deck.create_card(CardType.SKIP)
    third = game.deck.create_card(CardType.NORMAL)
    game.deck.cards = [first, second, third]
    game.game_state.cards_left_to_draw = game.deck.cards_left()
    stf_card = game.deck.create_card(CardType.SEE_THE_FUTURE)
    bot.add_card(stf_card)

    game.take_turn(bot)

    assert bot.seen == [first, second, third]
    assert game.deck.cards_left() == 3
    assert stf_card in game.deck.discard_pile
