import os
import importlib
import pygame
from managers.game_manager import GameManager
from render import Renderer
from bot_template import Bot

def main():
    test_mode = True
    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    width, height = screen.get_size()
    pygame.display.set_caption("Exploding Kittens Bot Battle")

    # Load bots
    bots = []
    if os.path.exists("bots"):
        for file in os.listdir("bots"):
            if file.endswith(".py") and file != "bot_template.py":
                module_name = file[:-3]
                module = importlib.import_module(f"bots.{module_name}")
                bot_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, Bot) and attr is not Bot:
                        bot_class = attr
                        break
                if bot_class:
                    bot_instance = bot_class()
                    bots.append(bot_instance)

    if not bots:
        print("No bots found in the /bots folder.")
        exit()

    # Create players and initialize game
    players = {bot.name: bot for bot in bots}
    game_manager = GameManager(players)
    renderer = Renderer(screen, width, height)

    # Main game loop
    running = True
    fps = pygame.time.Clock()
    while not game_manager.check_end_game() and running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        # Draw the table and display the current state
        renderer.draw_table(players, game_manager.state)
        renderer.display_message(f"Current Turn: {list(players.keys())[game_manager.state.current_player_index]}")

        # Play the turn
        for bot_name, bot in players.items():
            if bot_name not in game_manager.state.exploded_bots:
                try:
                    game_manager.play_turn(bot)
                except Exception as e:
                    print(f"Error during {bot.name}'s turn: {e}")
                    game_manager.state.exploded_bots.append(bot_name)

        pygame.display.flip()
        fps.tick(60)

    # Display the winner


    pygame.quit()

if __name__ == "__main__":
    main()