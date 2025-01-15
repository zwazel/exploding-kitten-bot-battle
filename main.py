import argparse
import copy

from bot_loader import load_bots
from card import CardCounts
from game_handling.game import Game
from collections import defaultdict


def main():
    parser = argparse.ArgumentParser(description="Exploding Kittens Lite")
    parser.add_argument("--test", action="store_true", help="Run in test mode")

    args = parser.parse_args()

    bots = load_bots("bots")

    if args.test:
        # duplicate the first bot in the list x times so that we have multiple bots (deepcopy)
        if len(bots) == 1:
            bots = [copy.deepcopy(bots[0]) for _ in range(4)]

            for i in range(len(bots)):
                bots[i].name = f"{bots[i].name}{i + 1}"

    amount_of_players = len(bots)

    card_counts = CardCounts(
        EXPLODING_KITTEN=amount_of_players - 1,
        DEFUSE=amount_of_players + int(amount_of_players / 2 + 0.5),
        SKIP=amount_of_players + 6,
        SEE_THE_FUTURE=amount_of_players * 2,
        # ATTACK=amount_of_players,
        NORMAL=amount_of_players * 6,
    )

    game = Game(args.test, bots, card_counts)

    if args.test:
        # Run the game x times
        x = 100  # You can set this to any number of iterations
        win_counts = defaultdict(int)

        for _ in range(x):
            game.reset(copy.deepcopy(card_counts), copy.deepcopy(bots))
            game.setup()
            winner = game.play()
            win_counts[winner.name] += 1

        # Print out the total wins and win percentage of each bot
        for bot_name, wins in win_counts.items():
            win_percentage = (wins / x) * 100
            print(f"{bot_name} wins: {wins} times, win percentage: {win_percentage:.2f}%")
    else:
        game.setup()
        winner = game.play()
        print(f"{winner.name} wins!")


if __name__ == "__main__":
    main()
