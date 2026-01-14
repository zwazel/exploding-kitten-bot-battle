#!/usr/bin/env python3
"""
Command-line interface for running Exploding Kitten bot battles.

Usage:
    python -m game.main
    python -m game.main --bots-dir ./bots
    python -m game.main --bot bots/my_bot.py:2 --bot bots/other_bot.py
    python -m game.main --history game.json --seed 42
    python -m game.main --stats --iterations 100   # Run statistics mode
    python -m game.main --stats --workers 8        # Parallel statistics with 8 workers
    python -m game.main --no-chat                  # Disable chat output
    python -m game.main --timeout 5                 # 5 second timeout per bot call
    python -m game.main --timeout 0                 # Disable timeout
"""

import argparse
import os
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED, TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

from game.engine import GameEngine
from game.bots.loader import BotLoader
from game.bots.base import Bot


# Module-level worker function for multiprocessing (must be picklable)
def _run_game_worker(args: tuple[list[tuple[str, int]], int, Path, float | None]) -> list[str]:
    """
    Worker function for running a single game in a separate process.
    
    Args:
        args: Tuple of (bot_specs, seed, deck_config_path, bot_timeout)
               bot_specs is list of (file_path, count) tuples
        
    Returns:
        List of player IDs in placement order.
    """
    import sys
    from io import StringIO
    from game.history import EventType
    
    bot_specs, seed, deck_config, bot_timeout = args
    
    # Suppress stdout to avoid bot loader messages cluttering output
    old_stdout = sys.stdout
    sys.stdout = StringIO()
    
    try:
        # Create engine WITHOUT timeout in worker processes.
        # Threads + multiprocessing can cause deadlocks on Windows.
        # Stats mode runs silent and fast, so timeout isn't needed.
        engine = GameEngine(seed=seed, quiet_mode=True, chat_enabled=False, bot_timeout=None)
        
        # Load bots fresh in this process
        loader = BotLoader()
        for file_path, count in bot_specs:
            path = Path(file_path)
            if path.exists():
                loaded = loader.load_from_file(path)
                if loaded:
                    bot_class = type(loaded[0])
                    engine.add_bot(loaded[0])
                    for _ in range(count - 1):
                        try:
                            engine.add_bot(bot_class())
                        except Exception:
                            pass
        
        # Create deck from config
        if deck_config.exists():
            deck = engine.registry.create_deck_from_file(deck_config)
            engine._state._draw_pile = deck
            engine._rng.shuffle(engine._state._draw_pile)
        
        # Run the game
        winner = engine.run()
        
        if not winner:
            return []
        
        # Extract elimination order from history
        elimination_order: list[str] = []
        for event in engine.history.get_events():
            if event.event_type == EventType.PLAYER_ELIMINATED:
                if event.player_id:
                    elimination_order.append(event.player_id)
        
        # Placement order: winner first, then reverse elimination order
        placements: list[str] = [winner] + list(reversed(elimination_order))
        
        return placements
    finally:
        sys.stdout = old_stdout


def _load_bots(args: argparse.Namespace, loader: BotLoader, verbose: bool = True) -> list[Bot]:
    """
    Load bots based on CLI arguments.
    
    Args:
        args: Parsed command line arguments.
        loader: Bot loader instance.
        verbose: Whether to print loading messages.
        
    Returns:
        List of loaded bot instances.
    """
    bots: list[Bot] = []
    
    # Load bots based on what's specified:
    # - Only --bot: use those bots only
    # - Only --bots-dir: use that directory
    # - Both: combine directory + individual bots
    # - Neither: use default ./bots directory
    
    has_bot_files = args.bot_files is not None and len(args.bot_files) > 0
    has_bots_dir = args.bots_dir is not None
    
    # Load from directory if specified or if nothing specified
    if has_bots_dir or (not has_bot_files and not has_bots_dir):
        bots_dir = args.bots_dir or Path("bots")
        if bots_dir.exists():
            dir_bots = loader.load_from_directory(bots_dir)
            bots.extend(dir_bots)
        elif has_bots_dir:
            if verbose:
                print(f"Error: Bot directory not found: {bots_dir}")
            return []
    
    # Load individual bot files if specified
    if has_bot_files:
        for bot_spec in args.bot_files:
            if ":" in bot_spec:
                path_str, count_str = bot_spec.rsplit(":", 1)
                count = int(count_str)
            else:
                path_str = bot_spec
                count = 1
            
            path = Path(path_str)
            if not path.exists():
                if verbose:
                    print(f"Error: Bot file not found: {path}")
                return []
            
            loaded = loader.load_from_file(path)
            if loaded:
                # Get the bot class from the first loaded instance
                bot_class = type(loaded[0])
                bots.append(loaded[0])  # Add the first instance
                # Create additional instances for the remaining count
                for i in range(count - 1):
                    try:
                        bots.append(bot_class())
                    except Exception as e:
                        if verbose:
                            print(f"Warning: Could not create additional instance of {bot_class.__name__}: {e}")
                        break
            elif verbose:
                print(f"Warning: No bot found in {path}")
    
    return bots


def _get_bot_classes(bots: list[Bot]) -> list[type[Bot]]:
    """Extract bot classes from bot instances for recreation in statistics mode."""
    return [type(bot) for bot in bots]


def _get_bot_specs(args: argparse.Namespace) -> list[tuple[str, int]]:
    """
    Extract bot file specifications from CLI arguments.
    
    Returns:
        List of (file_path, count) tuples for each bot.
    """
    specs: list[tuple[str, int]] = []
    
    has_bot_files = args.bot_files is not None and len(args.bot_files) > 0
    has_bots_dir = args.bots_dir is not None
    
    # Get bots from directory
    if has_bots_dir or (not has_bot_files and not has_bots_dir):
        bots_dir = args.bots_dir or Path("bots")
        if bots_dir.exists():
            for py_file in sorted(bots_dir.glob("*.py")):
                if not py_file.name.startswith("_"):
                    specs.append((str(py_file.absolute()), 1))
    
    # Get individual bot files
    if has_bot_files:
        for bot_spec in args.bot_files:
            if ":" in bot_spec:
                path_str, count_str = bot_spec.rsplit(":", 1)
                count = int(count_str)
            else:
                path_str = bot_spec
                count = 1
            
            path = Path(path_str)
            if path.exists():
                specs.append((str(path.absolute()), count))
    
    return specs


def _run_single_game(
    bot_classes: list[type[Bot]],
    seed: int,
    deck_config: Path,
    chat_enabled: bool,
    quiet_mode: bool,
) -> list[str]:
    """
    Run a single game with fresh bot instances.
    
    Args:
        bot_classes: List of bot classes to instantiate.
        seed: Random seed for this game.
        deck_config: Path to deck configuration.
        chat_enabled: Whether chat output is enabled.
        quiet_mode: Whether to suppress all console output.
        
    Returns:
        List of player IDs in placement order (index 0 = 1st place/winner,
        index -1 = last place/first eliminated). Empty list on error.
    """
    from game.history import EventType
    
    # Create engine
    engine = GameEngine(seed=seed, quiet_mode=quiet_mode, chat_enabled=chat_enabled)
    
    # Create fresh bot instances and add to engine
    player_ids: list[str] = []
    for bot_class in bot_classes:
        try:
            bot = bot_class()
            engine.add_bot(bot)
            # The engine assigns player IDs, we'll get them from the history later
        except Exception:
            return []
    
    # Create deck from config
    if deck_config.exists():
        deck = engine.registry.create_deck_from_file(deck_config)
        engine._state._draw_pile = deck
        engine._rng.shuffle(engine._state._draw_pile)
    
    # Run the game
    winner = engine.run()
    
    if not winner:
        return []
    
    # Extract elimination order from history
    elimination_order: list[str] = []
    for event in engine.history.get_events():
        if event.event_type == EventType.PLAYER_ELIMINATED:
            if event.player_id:
                elimination_order.append(event.player_id)
    
    # Placement order: winner first, then reverse elimination order (last eliminated = 2nd place)
    placements: list[str] = [winner] + list(reversed(elimination_order))
    
    return placements


def _run_verification(
    bot_specs: list[tuple[str, int]],
    bot_names: list[str],
    seed: int,
    deck_config: Path,
    bot_timeout: float,
) -> set[str]:
    """
    Run a verification game to detect bots that timeout.
    
    Runs a single game WITH timeout enabled. Any bot that times out
    during this verification is flagged for disqualification.
    
    Args:
        bot_specs: List of (file_path, count) tuples.
        bot_names: List of bot names (matching engine player IDs).
        seed: Random seed for the verification game.
        deck_config: Path to deck configuration.
        bot_timeout: Timeout in seconds.
        
    Returns:
        Set of bot names that timed out during verification.
    """
    from game.history import EventType
    
    print("\n" + "=" * 70)
    print("VERIFICATION RUN: Testing bots for timeouts...")
    print("=" * 70 + "\n")
    
    # Create engine WITH timeout for verification
    engine = GameEngine(seed=seed, quiet_mode=True, chat_enabled=False, bot_timeout=bot_timeout)
    
    # Load bots fresh
    loader = BotLoader()
    for file_path, count in bot_specs:
        path = Path(file_path)
        if path.exists():
            loaded = loader.load_from_file(path)
            if loaded:
                bot_class = type(loaded[0])
                engine.add_bot(loaded[0])
                for _ in range(count - 1):
                    try:
                        engine.add_bot(bot_class())
                    except Exception:
                        pass
    
    # Create deck from config
    if deck_config.exists():
        deck = engine.registry.create_deck_from_file(deck_config)
        engine._state._draw_pile = deck
        engine._rng.shuffle(engine._state._draw_pile)
    
    # Run the game
    engine.run()
    
    # Check history for timeout events
    timed_out_bots: set[str] = set()
    for event in engine.history.get_events():
        if event.event_type == EventType.BOT_TIMEOUT:
            if event.player_id:
                timed_out_bots.add(event.player_id)
                method = event.data.get("method", "unknown") if event.data else "unknown"
                print(f"  ⚠️ {event.player_id} timed out in {method}()")
    
    if timed_out_bots:
        print(f"\n  Found {len(timed_out_bots)} bot(s) with timeout issues.")
    else:
        print("  ✓ All bots passed verification (no timeouts detected)")
    
    return timed_out_bots


def _render_bar(value: int, max_value: int, width: int = 20) -> str:
    """Render an ASCII bar for a value."""
    if max_value == 0:
        return ""
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def run_statistics(
    args: argparse.Namespace,
    bot_specs: list[tuple[str, int]],
    bot_names: list[str],
    num_bots: int,
    base_seed: int,
    disqualified_bots: set[str] | None = None,
) -> None:
    """
    Run multiple games and collect statistics on placement.
    
    Args:
        args: Parsed CLI arguments.
        bot_specs: List of (file_path, count) tuples for loading bots.
        bot_names: List of bot names (for display/tracking).
        num_bots: Total number of bots.
        base_seed: Base seed for generating game seeds.
        disqualified_bots: Set of bot names that were disqualified during verification.
    """
    iterations = args.iterations
    disqualified_bots = disqualified_bots or set()
    
    # Track statistics: bot_name -> {place: count} where place is 1-indexed
    placements: dict[str, Counter[int]] = {}
    
    # Initialize placement counters
    for name in bot_names:
        placements[name] = Counter()
    
    # Create a mapping from player_id pattern to bot_name
    # The engine creates IDs like "BotName", "BotName_2", etc.
    
    print(f"\n{'='*70}")
    print(f"STATISTICS MODE: Running {iterations} games")
    print(f"Bots: {', '.join(bot_names)}")
    
    # Show disqualified bots if any
    if disqualified_bots:
        print(f"\n⚠️ DISQUALIFIED (timeout in verification): {', '.join(sorted(disqualified_bots))}")
    
    # Determine number of workers
    workers = getattr(args, 'workers', 1) or 1
    if workers > 1:
        print(f"Using {workers} parallel workers")
    print(f"{'='*70}\n")
    
    # Get timeout (0 means disabled)
    bot_timeout: float | None = args.timeout if args.timeout > 0 else None
    
    # Prepare all game arguments (pass bot_specs instead of bot_classes)
    game_args: list[tuple[list[tuple[str, int]], int, Path, float | None]] = [
        (bot_specs, (base_seed + i) % (2**31), args.deck_config, bot_timeout)
        for i in range(iterations)
    ]
    
    completed = 0
    progress_step = max(1, iterations // 10)
    
    # Per-game timeout: 10 seconds max for any single game
    # This prevents stuck workers from blocking the entire stats run
    GAME_TIMEOUT_SECONDS = 10
    timed_out_games = 0
    
    if workers > 1:
        # Parallel execution with ProcessPoolExecutor
        # Use wait() with timeout to handle stuck workers properly
        with ProcessPoolExecutor(max_workers=workers) as executor:
            # Submit all tasks
            pending = {executor.submit(_run_game_worker, arg) for arg in game_args}
            
            # Maximum time to wait for ALL remaining games before giving up
            MAX_TOTAL_WAIT = 300  # 5 minutes max for all remaining games
            start_time = time.time()
            
            while pending:
                # Wait for at least one future to complete, with a short timeout
                done, pending = wait(pending, timeout=GAME_TIMEOUT_SECONDS, return_when=FIRST_COMPLETED)
                
                # Process completed futures
                for future in done:
                    try:
                        game_placements = future.result(timeout=0)  # Already done, should be instant
                    except Exception:
                        # Handle any errors gracefully
                        completed += 1
                        continue
                    
                    # Record placements
                    for place, player_id in enumerate(game_placements, 1):
                        if player_id in placements:
                            placements[player_id][place] += 1
                    
                    completed += 1
                    
                    # Progress indicator
                    if iterations >= 10 and completed % progress_step == 0:
                        print(f"  Progress: {completed * 100 // iterations}% ({completed}/{iterations} games)")
                
                # Check if we got no completions (all remaining are stuck)
                if not done and pending:
                    elapsed = time.time() - start_time
                    if elapsed > MAX_TOTAL_WAIT:
                        # Give up on remaining games
                        timed_out_games = len(pending)
                        completed += timed_out_games
                        print(f"  ⚠️ {timed_out_games} games timed out - cancelling remaining workers")
                        for future in pending:
                            future.cancel()
                        break
                    else:
                        # Some games are slow but we haven't hit total limit yet
                        print(f"  ⏳ Waiting for {len(pending)} slow games... ({int(elapsed)}s elapsed)")
    else:
        # Sequential execution (original behavior)
        for i, arg in enumerate(game_args):
            game_placements = _run_game_worker(arg)
            
            # Record placements
            for place, player_id in enumerate(game_placements, 1):
                if player_id in placements:
                    placements[player_id][place] += 1
            
            completed += 1
            
            # Progress indicator
            if iterations >= 10 and completed % progress_step == 0:
                print(f"  Progress: {completed * 100 // iterations}% ({completed}/{iterations} games)")
            elif iterations < 10:
                print(f"  Game {completed}/{iterations} complete")
    
    # Print results
    print(f"\n{'='*70}")
    print("STATISTICS RESULTS")
    print(f"{'='*70}")
    print(f"\nTotal games: {iterations}")
    if timed_out_games > 0:
        successful_games = iterations - timed_out_games
        print(f"⚠️ Games timed out: {timed_out_games} (stats based on {successful_games} successful games)")
    print(f"Players: {num_bots}\n")
    
    # Calculate max name length for formatting
    max_name_len = max(len(name) for name in bot_names) if bot_names else 10
    
    # Sort by wins (1st place count, descending)
    sorted_bots = sorted(bot_names, key=lambda n: placements[n][1], reverse=True)
    
    # Print win summary
    print("=== WIN SUMMARY ===\n")
    print(f"{'Bot Name':<{max_name_len}}  {'Wins':>6}  {'Win Rate':>10}")
    print("-" * (max_name_len + 20))
    
    for bot_name in sorted_bots:
        wins = placements[bot_name][1]
        win_rate = (wins / iterations) * 100
        print(f"{bot_name:<{max_name_len}}  {wins:>6}  {win_rate:>9.1f}%")
    
    # Print placement breakdown with ASCII bars
    print(f"\n{'='*70}")
    print("=== PLACEMENT BREAKDOWN ===\n")
    
    # Header row with place numbers
    place_header = "  ".join(f"{p}{'st' if p==1 else 'nd' if p==2 else 'rd' if p==3 else 'th':>5}" for p in range(1, num_bots + 1))
    print(f"{'Bot Name':<{max_name_len}}  {place_header}")
    print("-" * (max_name_len + 8 * num_bots))
    
    for bot_name in sorted_bots:
        place_counts = "  ".join(f"{placements[bot_name][p]:>5}" for p in range(1, num_bots + 1))
        print(f"{bot_name:<{max_name_len}}  {place_counts}")
    
    # Print ASCII bar charts for each bot
    print(f"\n{'='*70}")
    print("=== PLACEMENT DISTRIBUTION (ASCII) ===\n")
    
    bar_width = 30
    
    for bot_name in sorted_bots:
        print(f"{bot_name}:")
        bot_placements = placements[bot_name]
        
        for place in range(1, num_bots + 1):
            count = bot_placements[place]
            percentage = (count / iterations) * 100
            bar = _render_bar(count, iterations, bar_width)
            place_label = f"{place}{'st' if place==1 else 'nd' if place==2 else 'rd' if place==3 else 'th'}"
            print(f"  {place_label:>4}: {bar} {count:>4} ({percentage:>5.1f}%)")
        print()
    
    print(f"{'='*70}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an Exploding Kitten bot battle",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m game.main                                 # Load all bots from ./bots
  python -m game.main --bot bots/my_bot.py:3          # 3 copies of my_bot
  python -m game.main --bot bot1.py --bot bot2.py:2   # 1 bot1, 2 bot2s
  python -m game.main --seed 42 --history game.json   # Reproducible with history
  python -m game.main --stats --iterations 100        # Run 100 games for statistics
  python -m game.main --no-chat                       # Disable chat output
        """,
    )
    parser.add_argument(
        "--bots-dir",
        type=Path,
        default=None,
        help="Directory containing bot implementations (default: ./bots if no --bot specified)",
    )
    parser.add_argument(
        "--bot",
        action="append",
        dest="bot_files",
        metavar="FILE[:COUNT]",
        help="Bot file to load (can specify multiple). Format: path/to/bot.py or path/to/bot.py:3 for 3 copies",
    )
    parser.add_argument(
        "--deck-config",
        type=Path,
        default=Path("configs/default_deck.json"),
        help="Path to deck configuration JSON file",
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=None,
        help="Path to save game history JSON",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic gameplay (random if not specified)",
    )
    parser.add_argument(
        "--hand-size",
        type=int,
        default=7,
        help="Initial hand size for each player",
    )
    # Statistics mode arguments
    parser.add_argument(
        "--stats",
        action="store_true",
        default=False,
        help="Run in statistics mode: run multiple games and collect win statistics",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=100,
        help="Number of games to run in statistics mode (default: 100)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of parallel workers for statistics mode (default: CPU count)",
    )
    # Chat control argument
    parser.add_argument(
        "--no-chat",
        action="store_true",
        default=False,
        help="Disable chat message output (keeps game logs clean)",
    )
    # Timeout argument
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="Bot timeout in seconds (0 to disable). Bots that take too long are eliminated. Default: 5.0",
    )
    
    args = parser.parse_args()
    
    # Generate random seed if not specified
    seed: int = args.seed if args.seed is not None else int(time.time() * 1000) % (2**31)
    
    # Load bots
    loader = BotLoader()
    bots = _load_bots(args, loader, verbose=True)
    
    if not bots:
        return
    
    print(f"Total bots loaded: {len(bots)}")
    
    if len(bots) < 2:
        print(f"Error: Need at least 2 bots, found {len(bots)}")
        return
    
    # Statistics mode
    if args.stats:
        # Set default workers to CPU count if not specified
        if args.workers is None:
            args.workers = os.cpu_count() or 4
        
        # Get bot specs for multiprocessing
        bot_specs = _get_bot_specs(args)
        
        # Get bot names from loaded bots (matching engine naming convention)
        bot_names: list[str] = []
        for bot in bots:
            base_name = bot.name
            name = base_name
            suffix = 1
            while name in bot_names:
                suffix += 1
                name = f"{base_name}_{suffix}"
            bot_names.append(name)
        
        # Get timeout (0 means disabled)
        bot_timeout: float = args.timeout if args.timeout > 0 else 5.0
        
        # Run verification to detect slow bots
        disqualified = _run_verification(
            bot_specs, bot_names, seed, args.deck_config, bot_timeout
        )
        
        # Filter out disqualified bots from specs and names
        if disqualified:
            # Find which base bot types timed out (strip suffixes like "_2", "_3")
            disqualified_base_names: set[str] = set()
            for name in disqualified:
                # Extract base name (before any _N suffix)
                parts = name.rsplit("_", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    disqualified_base_names.add(parts[0])
                else:
                    disqualified_base_names.add(name)
            
            # Filter bot_specs to remove disqualified bot files
            new_bot_specs: list[tuple[str, int]] = []
            for file_path, count in bot_specs:
                # Load bot to check its name
                temp_loader = BotLoader()
                temp_bots = temp_loader.load_from_file(Path(file_path))
                if temp_bots:
                    bot_base_name = temp_bots[0].name
                    if bot_base_name not in disqualified_base_names:
                        new_bot_specs.append((file_path, count))
            
            bot_specs = new_bot_specs
            
            # Filter bot_names to remove disqualified
            bot_names = [n for n in bot_names if n not in disqualified]
            
            if len(bot_names) < 2:
                print("\n❌ ERROR: Not enough bots remaining after disqualification!")
                print("   At least 2 bots are required for statistics.")
                return
        
        run_statistics(args, bot_specs, bot_names, len(bot_names), seed, disqualified)
        return
    
    # Normal single-game mode
    print(f"Using seed: {seed}")
    
    # Create engine with chat and timeout settings
    chat_enabled = not args.no_chat
    bot_timeout: float | None = args.timeout if args.timeout > 0 else None
    engine = GameEngine(seed=seed, chat_enabled=chat_enabled, bot_timeout=bot_timeout)
    
    # Add bots
    for bot in bots:
        engine.add_bot(bot)
    
    # Create deck from config
    if args.deck_config.exists():
        deck = engine.registry.create_deck_from_file(args.deck_config)
        engine._state._draw_pile = deck
        engine._rng.shuffle(engine._state._draw_pile)
        print(f"Loaded deck with {len(deck)} cards from {args.deck_config}")
    else:
        print(f"Warning: Deck config not found at {args.deck_config}, using default")
    
    # Run the game
    print(f"\n{'='*50}")
    print("Starting game!")
    print(f"{'='*50}\n")
    
    winner = engine.run(history_file=args.history)
    
    print(f"\n{'='*50}")
    if winner:
        print(f"Winner: {winner}")
    else:
        print("No winner (game ended abnormally)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
