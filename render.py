"""
All drawing code (Pygame-specific) is in this file, such as drawing the table, player cards, etc.
"""
import pygame

class Renderer:
    def __init__(self, screen, width, height):
        self.screen = screen
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont(None, 40)

    def draw_table(self, players, state):
        WHITE = (255, 255, 255)
        GRAY = (200, 200, 200)
        RED = (255, 0, 0)
        GREEN = (0, 255, 0)
        BLUE = (0, 0, 255)

        self.screen.fill(WHITE)
        table_radius = min(self.width, self.height) // 4
        pygame.draw.circle(self.screen, GRAY, (self.width // 2, self.height // 2), table_radius)

        # Draw players in a circle
        num_players = len(players)
        angle_increment = 2 * 3.14159 / num_players

        for i, (name, player) in enumerate(players.items()):
            angle = i * angle_increment - 3.14159 / 2  # Start at 12 o'clock
            bot_x = self.width // 2 + int(table_radius * 1.2 * pygame.math.cos(angle))
            bot_y = self.height // 2 + int(table_radius * 1.2 * pygame.math.sin(angle))
            bot_text = self.font.render(name, True, (0, 0, 0))
            self.screen.blit(bot_text, (bot_x - bot_text.get_width() // 2, bot_y - 20))

            # Draw hand cards
            card_x = bot_x - len(player.hand) * 35 // 2
            for card in player.hand:
                color = RED if card == "Exploding Kitten" else GREEN if card == "Defuse" else BLUE
                pygame.draw.rect(self.screen, color, (card_x, bot_y, 70, 40))
                card_text = self.font.render(card, True, WHITE)
                self.screen.blit(card_text, (card_x + 5, bot_y + 5))
                card_x += 80

    def display_message(self, message):
        message_text = self.font.render(message, True, (0, 0, 0))
        self.screen.blit(message_text, ((self.width - message_text.get_width()) // 2, 10))