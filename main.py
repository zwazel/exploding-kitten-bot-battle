from bot_loader import load_bots
from game import Game
from card import CardCounts

def main():
    bots = load_bots("bots")
    card_counts = CardCounts(
        EXPLODING_KITTEN=0,  # This will be set based on the number of players
        DEFUSE=6,
        SKIP=4,
        ATTACK=4,
        SEE_THE_FUTURE=5,
        NORMAL=20
    )

    game = Game(bots, card_counts)
    game.setup()
    winner = game.play()
    print(f"The winner is: {winner.name}")

if __name__ == "__main__":
    main()