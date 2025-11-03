"""Main entry point for Exploding Kittens Bot Battle."""

import os
import sys
import importlib.util
import argparse
from typing import List
from datetime import datetime
from game import Bot, GameEngine, ReplayRecorder


def load_bots_from_directory(directory: str = "bots") -> List[Bot]:
    """
    Load all bot classes from Python files in the specified directory.
    
    Args:
        directory: Directory containing bot files
        
    Returns:
        List of instantiated bot objects
    """
    bots = []
    bot_dir = os.path.join(os.path.dirname(__file__), directory)
    
    if not os.path.exists(bot_dir):
        print(f"Error: Bot directory '{bot_dir}' does not exist")
        return bots
    
    # Get all .py files in the bots directory
    bot_files = [f for f in os.listdir(bot_dir) if f.endswith('.py') and not f.startswith('__')]
    
    if not bot_files:
        print(f"Warning: No bot files found in '{bot_dir}'")
        return bots
    
    for filename in bot_files:
        bot_name = filename[:-3]  # Remove .py extension
        file_path = os.path.join(bot_dir, filename)
        
        try:
            # Load the module dynamically
            spec = importlib.util.spec_from_file_location(bot_name, file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Find the Bot class in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        issubclass(attr, Bot) and 
                        attr is not Bot):
                        # Instantiate the bot
                        bot_instance = attr(bot_name)
                        bots.append(bot_instance)
                        print(f"Loaded bot: {bot_name}")
                        break
        except Exception as e:
            print(f"Error loading bot from {filename}: {e}")
    
    return bots


def main() -> None:
    """Main function to run the Exploding Kittens bot battle."""
    parser = argparse.ArgumentParser(description='Exploding Kittens Bot Battle')
    parser.add_argument('--test', action='store_true', 
                       help='Run in test mode (auto-play without user input)')
    parser.add_argument('--replay', type=str, metavar='FILENAME',
                       help='Enable replay recording and save to specified file (e.g., replay.json)')
    args = parser.parse_args()
    
    # Load bots
    print("Loading bots...")
    bots = load_bots_from_directory()
    
    if not bots:
        print("Error: No bots loaded. Please add bot files to the 'bots' directory.")
        sys.exit(1)
    
    # Handle test mode
    if args.test:
        if len(bots) == 1:
            # Duplicate the single bot for testing
            bot_class = type(bots[0])
            duplicate_bot = bot_class(f"{bots[0].name}_copy")
            bots.append(duplicate_bot)
            print(f"Test mode: Duplicated {bots[0].name} to play against itself")
    
    if len(bots) < 2:
        print("Error: Need at least 2 bots to play. Load more bots or use --test flag.")
        sys.exit(1)
    
    # Create replay recorder if requested
    replay_recorder = None
    replay_filename = None
    if args.replay:
        replay_filename = args.replay
        replay_recorder = ReplayRecorder([bot.name for bot in bots], enabled=True)
        print(f"Replay recording enabled. Will save to: {replay_filename}")
    
    # Create and run the game
    game = GameEngine(bots, verbose=True, replay_recorder=replay_recorder)
    
    # Run the game (both modes run automatically for now)
    winner = game.play_game()
    
    # Save replay if recording was enabled
    if replay_recorder and replay_filename:
        try:
            replay_recorder.save_to_file(replay_filename)
            print(f"\n✅ Replay saved to: {replay_filename}")
        except Exception as e:
            print(f"\n❌ Error saving replay: {e}")
    
    if winner:
        print(f"\n🏆 Victory goes to: {winner.name}! 🏆")
    else:
        print("\nGame ended with no winner.")


if __name__ == "__main__":
    main()
