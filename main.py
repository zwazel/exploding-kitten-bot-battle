import argparse
import copy

from card import CardCounts
from bot_loader import load_bots
from game_handling.game import Game


def main():
    parser = argparse.ArgumentParser(description="Exploding Kittens Lite")
    parser.add_argument("--test", action="store_true", help="Run in test mode")

    args = parser.parse_args()

    bots = load_bots("bots")

    if args.test:
        # duplicate the first bot in the list x times so that we have multiple bots (deepcopy)
        bots = [copy.deepcopy(bots[0]) for _ in range(4)]

        for i in range(len(bots)):
            bots[i].name = f"{bots[i].name}{i + 1}"

    amount_of_players = len(bots)

    card_counts = CardCounts(
        EXPLODING_KITTEN=amount_of_players - 1,
        DEFUSE=amount_of_players + 4,
        SKIP=amount_of_players + 6,
        SEE_THE_FUTURE=amount_of_players * 2,
        # ATTACK=amount_of_players,
        NORMAL=amount_of_players * 6,
    )

    game = Game(bots, card_counts)
    game.setup()
    winner = game.play()
    print(f"{winner.name} wins!")


if __name__ == "__main__":
    main()
