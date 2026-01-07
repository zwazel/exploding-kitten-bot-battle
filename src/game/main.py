#!/usr/bin/env python3
"""
Command-line interface for running Exploding Kitten bot battles.

Usage:
    python -m game.main
    python -m game.main --bots-dir ./bots
    python -m game.main --bot bots/my_bot.py:2 --bot bots/other_bot.py
    python -m game.main --history game.json --seed 42
"""

import argparse
import time
from pathlib import Path

from game.engine import GameEngine
from game.bots.loader import BotLoader


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
    
    args = parser.parse_args()
    
    # Generate random seed if not specified
    seed: int = args.seed if args.seed is not None else int(time.time() * 1000) % (2**31)
    print(f"Using seed: {seed}")
    
    # Load bots
    loader = BotLoader()
    bots = []
    
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
            print(f"Error: Bot directory not found: {bots_dir}")
            return
    
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
                print(f"Error: Bot file not found: {path}")
                return
            
            for i in range(count):
                loaded = loader.load_from_file(path)
                if loaded:
                    bot_instance = loaded[0]
                    bots.append(bot_instance)
                else:
                    print(f"Warning: No bot found in {path}")
                    break
    
    print(f"Total bots loaded: {len(bots)}")
    
    if len(bots) < 2:
        print(f"Error: Need at least 2 bots, found {len(bots)}")
        return
    
    # Create engine
    engine = GameEngine(seed=seed)
    
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
        print(f"🎉 Winner: {winner}")
    else:
        print("No winner (game ended abnormally)")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
