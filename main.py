"""Main entry point for Exploding Kittens Bot Battle."""

import os
import sys
import importlib.util
import argparse
import multiprocessing
from typing import List, Optional, Tuple
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
    parser.add_argument('--parallel', action='store_true',
                       help='Run games in parallel using multiple CPU cores (only for statistics mode)')
    args = parser.parse_args()
    
    # Validate incompatible flags
    if args.replay and args.stats is not None:
        print("Error: --replay and --stats flags are incompatible. Use one or the other.")
        sys.exit(1)
    
    # Validate that --parallel is only used with --stats
    if args.parallel and args.stats is None:
        print("Error: --parallel flag can only be used with --stats mode.")
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
        # Validate that --parallel is only used with --stats
        if args.parallel and args.stats is None:
            print("Error: --parallel flag can only be used with --stats mode.")
            sys.exit(1)
        
        # args.stats is empty string when flag is used without filename, or a string with the filename
        output_file = args.stats if args.stats else None
        run_statistics_mode(bots, args.runs, output_file, parallel=args.parallel)
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


def _run_single_game(bot_info: List[Tuple[str, str]]) -> List[Tuple[str, int]]:
    """
    Worker function to run a single game. Used for parallel execution.
    
    Args:
        bot_info: List of (bot_module_path, bot_name) tuples
        
    Returns:
        List of (bot_name, placement) tuples for this game
    """
    # Import bot classes from the bots directory
    bots = []
    bot_dir = os.path.join(os.path.dirname(__file__), "bots")
    
    for module_path, bot_name in bot_info:
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(bot_name, module_path)
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
                    break
    
    # Run the game in silent mode
    game = GameEngine(bots, verbose=False)
    game.play_game()
    
    # Return placements
    return game.get_placements()


def run_statistics_mode(bot_templates: List[Bot], num_runs: int, output_file: Optional[str] = None, parallel: bool = False) -> None:
    """
    Run multiple games and collect statistics.
    
    Args:
        bot_templates: List of bot instances to use as templates
        num_runs: Number of games to run
        output_file: Optional path to save statistics JSON file. If None, only displays stats.
        parallel: Whether to run games in parallel using multiprocessing
    """
    print(f"\nRunning {num_runs} games for statistics...")
    print(f"Bots: {', '.join(bot.name for bot in bot_templates)}")
    if parallel:
        cpu_count = multiprocessing.cpu_count()
        print(f"Parallel mode enabled: using {cpu_count} CPU cores")
    print("=" * 70)
    
    stats = GameStatistics()
    
    if parallel:
        # Parallel execution using multiprocessing
        # Prepare bot info for worker processes
        bot_info = []
        bot_dir = os.path.join(os.path.dirname(__file__), "bots")
        for bot_template in bot_templates:
            # Find the source file for this bot
            bot_name = bot_template.name
            file_path = os.path.join(bot_dir, f"{bot_name}.py")
            if os.path.exists(file_path):
                bot_info.append((file_path, bot_name))
        
        # Fall back to sequential if bot files don't exist (e.g., for test bots)
        if len(bot_info) < 2:
            print("Warning: Bot files not found in bots/ directory. Falling back to sequential mode.")
            parallel = False
        
    if parallel:
        # Create work items (each is the same bot_info list)
        work_items = [bot_info] * num_runs
        
        # Use multiprocessing Pool to run games in parallel
        cpu_count = multiprocessing.cpu_count()
        with multiprocessing.Pool(processes=cpu_count) as pool:
            # Use imap_unordered for better progress tracking
            results = []
            completed = 0
            for placements in pool.imap_unordered(_run_single_game, work_items, chunksize=max(1, num_runs // (cpu_count * 4))):
                stats.record_game(placements)
                completed += 1
                
                # Show progress
                if completed % max(1, num_runs // 10) == 0 or completed == num_runs:
                    percentage = (completed / num_runs) * 100
                    print(f"Progress: {completed}/{num_runs} games completed ({percentage:.1f}%)")
    
    if not parallel:
        # Sequential execution (original implementation)
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
