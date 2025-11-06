"""Main entry point for Exploding Kittens Bot Battle."""

import os
import sys
import importlib.util
import argparse
from typing import List, Optional
from game import Bot, GameEngine, ReplayRecorder, GameStatistics


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
    parser.add_argument('--stats', nargs='?', const='', type=str, metavar='FILENAME',
                       help='Run multiple games and display statistics. Optionally save to file (e.g., stats.json)')
    parser.add_argument('--runs', type=int, default=100, metavar='N',
                       help='Number of games to run in statistics mode (default: 100)')
    args = parser.parse_args()
    
    # Validate incompatible flags
    if args.replay and args.stats:
        print("Error: --replay and --stats flags are incompatible. Use one or the other.")
        sys.exit(1)
    
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
    
    # Statistics mode
    if args.stats is not None:
        # args.stats is empty string when flag is used without filename, or a string with the filename
        output_file = args.stats if args.stats else None
        run_statistics_mode(bots, args.runs, output_file)
        return
    
    # Single game mode (with optional replay)
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


def run_statistics_mode(bot_templates: List[Bot], num_runs: int, output_file: Optional[str] = None) -> None:
    """
    Run multiple games and collect statistics.
    
    Args:
        bot_templates: List of bot instances to use as templates
        num_runs: Number of games to run
        output_file: Optional path to save statistics JSON file. If None, only displays stats.
    """
    print(f"\nRunning {num_runs} games for statistics...")
    print(f"Bots: {', '.join(bot.name for bot in bot_templates)}")
    print("=" * 70)
    
    stats = GameStatistics()
    
    for run_num in range(1, num_runs + 1):
        # Create fresh bot instances for each game
        bots = []
        for bot_template in bot_templates:
            bot_class = type(bot_template)
            new_bot = bot_class(bot_template.name)
            bots.append(new_bot)
        
        # Run the game in silent mode (verbose=False)
        game = GameEngine(bots, verbose=False)
        winner = game.play_game()
        
        # Record results
        placements = game.get_placements()
        stats.record_game(placements)
        
        # Show progress
        if run_num % 10 == 0 or run_num == num_runs:
            percentage = (run_num / num_runs) * 100
            print(f"Progress: {run_num}/{num_runs} games completed ({percentage:.1f}%)")
    
    print("=" * 70)
    print("All games completed!\n")
    
    # Display summary statistics
    stats.print_summary()
    
    # Save to file if filename was provided
    if output_file:
        try:
            stats.save_to_file(output_file)
            print(f"\n✅ Statistics saved to: {output_file}")
        except Exception as e:
            print(f"\n❌ Error saving statistics: {e}")


if __name__ == "__main__":
    main()
