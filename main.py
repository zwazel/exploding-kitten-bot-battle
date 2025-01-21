""" Main file for running the Exploding Kittens game """
import argparse
import copy
from collections import defaultdict

from bot_loader import load_bots
from card import CardCounts
from game_handling.game import Game


def main() -> None:
    """
    Main function
    :return: None
    """
    parser = argparse.ArgumentParser(description='Exploding Kittens Lite')
    parser.add_argument('--test', action='store_true', help='Run in test mode')

    args = parser.parse_args()

    bots = load_bots('bots')

    if args.test:
        # duplicate the first bot in the list x times so that we have multiple bots (deepcopy)
        if len(bots) == 1:
            bots = [copy.deepcopy(bots[0]) for _ in range(4)]

            for i in range(len(bots)):
                bots[i].name = f'{bots[i].name}{i + 1}'

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
        point_counts = defaultdict(int)

        for _ in range(x):
            game.reset(copy.deepcopy(card_counts), copy.deepcopy(bots))
            game.setup()
            winner = game.play()

            for i in range(len(game.ranking)):
                # Each bot gets points based on their standing
                point_counts[game.ranking[i].name] += i
            win_counts[winner.name] += 1
            point_counts[winner.name] += len(game.ranking)

        # Print out the total wins and win percentage of each bot
        sorted_win_counts = sorted(win_counts.items(), key=lambda item: (item[1] / x) * 100,
                                   reverse=True)
        for bot_name, wins in sorted_win_counts:
            win_percentage = (wins / x) * 100
            print(f'{bot_name:30} wins: {wins} times, win percentage: {win_percentage:.2f}%')

        # Print out the total points of each bot
        print('\nTotal points for each bot:')
        sorted_points_counts = sorted(point_counts.items(), key=lambda item: item[1], reverse=True)
        for bot_name, points in sorted_points_counts:
            print(f'{bot_name:30} {points} points')
    else:
        game.setup()
        winner = game.play()
        print(f'{winner.name} wins!')
        print(f'{game.ranking}')


if __name__ == '__main__':
    main()
