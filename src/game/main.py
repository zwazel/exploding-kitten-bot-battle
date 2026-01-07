#!/usr/bin/env python3
"""
Command-line interface for running Exploding Kitten bot battles.

Usage:
    python -m game.main
    python -m game.main --bots-dir ./bots
    python -m game.main --bot bots/my_bot.py:2 --bot bots/other_bot.py
    python -m game.main --history game.json --seed 42
    python -m game.main --stats --iterations 100   # Run statistics mode
    python -m game.main --no-chat                  # Disable chat output
"""

import argparse
import time
from collections import Counter
from pathlib import Path

from game.engine import GameEngine
from game.bots.loader import BotLoader
from game.bots.base import Bot


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


def _render_bar(value: int, max_value: int, width: int = 20) -> str:
    """Render an ASCII bar for a value."""
    if max_value == 0:
        return ""
    filled = int((value / max_value) * width)
    return "█" * filled + "░" * (width - filled)


def run_statistics(
    args: argparse.Namespace,
    bot_classes: list[type[Bot]],
    base_seed: int,
) -> None:
    """
    Run multiple games and collect statistics on placement.
    
    Args:
        args: Parsed CLI arguments.
        bot_classes: List of bot classes to use.
        base_seed: Base seed for generating game seeds.
    """
    iterations = args.iterations
    num_bots = len(bot_classes)
    
    # Track statistics: bot_name -> {place: count} where place is 1-indexed
    placements: dict[str, Counter[int]] = {}
    bot_names: list[str] = []
    
    # Get bot names by creating temporary instances
    for i, bot_class in enumerate(bot_classes):
        try:
            temp_bot = bot_class()
            # Handle duplicate names by suffixing with index
            base_name = temp_bot.name
            name = base_name
            suffix = 1
            while name in bot_names:
                suffix += 1
                name = f"{base_name}_{suffix}"
            bot_names.append(name)
        except Exception:
            bot_names.append(f"Bot_{i}")
    
    # Initialize placement counters
    for name in bot_names:
        placements[name] = Counter()
    
    # Create a mapping from player_id pattern to bot_name
    # The engine creates IDs like "BotName", "BotName_2", etc.
    
    print(f"\n{'='*70}")
    print(f"STATISTICS MODE: Running {iterations} games")
    print(f"Bots: {', '.join(bot_names)}")
    print(f"{'='*70}\n")
    
    # Run games
    for i in range(iterations):
        # Generate unique seed for each iteration
        seed = (base_seed + i) % (2**31)
        
        game_placements = _run_single_game(
            bot_classes=bot_classes,
            seed=seed,
            deck_config=args.deck_config,
            chat_enabled=False,  # Always disable chat in stats mode
            quiet_mode=True,      # Always quiet in stats mode
        )
        
        # Record placements
        for place, player_id in enumerate(game_placements, 1):
            if player_id in placements:
                placements[player_id][place] += 1
        
        # Progress indicator (every 10% or every game if < 10)
        if iterations >= 10:
            if (i + 1) % (iterations // 10) == 0:
                print(f"  Progress: {(i + 1) * 100 // iterations}% ({i + 1}/{iterations} games)")
        else:
            print(f"  Game {i + 1}/{iterations} complete")
    
    # Print results
    print(f"\n{'='*70}")
    print("STATISTICS RESULTS")
    print(f"{'='*70}")
    print(f"\nTotal games: {iterations}")
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
    # Chat control argument
    parser.add_argument(
        "--no-chat",
        action="store_true",
        default=False,
        help="Disable chat message output (keeps game logs clean)",
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
        bot_classes = _get_bot_classes(bots)
        run_statistics(args, bot_classes, seed)
        return
    
    # Normal single-game mode
    print(f"Using seed: {seed}")
    
    # Create engine with chat setting
    chat_enabled = not args.no_chat
    engine = GameEngine(seed=seed, chat_enabled=chat_enabled)
    
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
