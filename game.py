import os
import pygame
import random
import importlib
import math

def main():
    # Mode Configuration
    TEST_MODE = True  # Set to False for "real" mode
    BOT_COPIES = 4  # Number of times each bot should be duplicated in test mode

    # Initialize pygame
    pygame.init()

    # Screen settings
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()
    pygame.display.set_caption("Exploding Kittens Bot Battle")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (200, 200, 200)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    # Font
    font = pygame.font.SysFont(None, 40)

    # Game Configuration
    NUM_CARDS_TO_REMEMBER = 5
    EXPLOSIONS = -1  # Adjusted automatically to players - 1
    CARD_TYPES = ["Exploding Kitten", "Defuse", "Skip", "Attack", "See the Future", "Normal"]

    # Bot Handling
    bots = []
    bot_names = []
    bot_folder = "bots"

    # Load Bots
    if os.path.exists(bot_folder):
        for file in os.listdir(bot_folder):
            if file.endswith(".py"):
                module_name = file[:-3]
                module = importlib.import_module(f"bots.{module_name}")
                bot_instance = module.Bot()
                if TEST_MODE:
                    for i in range(BOT_COPIES):
                        bots.append(module.Bot())
                        bot_names.append(f"{bot_instance.name}_{i + 1}")
                else:
                    bots.append(bot_instance)
                    bot_names.append(bot_instance.name)

    if not bots:
        print("No bots found in the bots/ folder.")
        exit()

    # Game State
    class GameState:
        def __init__(self, players):
            self.players = players
            self.draw_pile = []
            self.discard_pile = []
            self.exploded_bots = []
            self.current_player_index = 0
            self.last_played_cards = []

        def initialize_deck(self):
            num_players = len(self.players)
            self.draw_pile = (
                    ["Exploding Kitten"] * (num_players - 1) +
                    ["Defuse"] * num_players +
                    ["Skip"] * (num_players * 2) +
                    ["Attack"] * (num_players * 2) +
                    ["See the Future"] * num_players +
                    ["Normal"] * (num_players * 3)
            )
            random.shuffle(self.draw_pile)

        def get_visible_state(self, player_name):
            return {
                "hand": self.players[player_name].hand,
                "remaining_draw_cards": len(self.draw_pile),
                "discard_pile": self.discard_pile[-NUM_CARDS_TO_REMEMBER:],
                "card_counts": {card_type: self.draw_pile.count(card_type) + self.discard_pile.count(card_type) for card_type in CARD_TYPES},
            }

    # Bot class template
    class Player:
        def __init__(self, name):
            self.name = name
            self.hand = []

    # Create players
    players = {name: Player(name) for name in bot_names}
    state = GameState(players)
    state.initialize_deck()

    # Draw the game table
    def draw_table():
        screen.fill(WHITE)

        # Draw round table in the center
        table_radius = min(width, height) // 4
        pygame.draw.circle(screen, GRAY, (width // 2, height // 2), table_radius)

        # Arrange bots around the circle
        num_players = len(players)
        angle_increment = 2 * math.pi / num_players

        for i, (name, player) in enumerate(players.items()):
            angle = i * angle_increment - math.pi / 2  # Start at the top (12 o'clock position)
            bot_x = width // 2 + int(math.cos(angle) * (table_radius + 50))
            bot_y = height // 2 + int(math.sin(angle) * (table_radius + 50))

            # Draw bot name
            bot_text = font.render(name, True, BLACK)
            screen.blit(bot_text, (bot_x - bot_text.get_width() // 2, bot_y - 30))

            # Draw hand cards as rectangles
            card_x = bot_x - len(player.hand) * 35 // 2
            for card in player.hand:
                color = RED if card == "Exploding Kitten" else GREEN if card == "Defuse" else BLUE
                pygame.draw.rect(screen, color, (card_x, bot_y, 70, 40))
                card_text = font.render(card, True, WHITE)
                screen.blit(card_text, (card_x + 5, bot_y + 5))
                card_x += 80

    # Main Game Loop
    running = True
    fps = pygame.time.Clock()
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        draw_table()
        pygame.display.flip()
        fps.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
