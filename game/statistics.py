"""Statistics tracking and analysis for bot battle games."""

import json
from typing import List, Dict, Optional
from collections import defaultdict


class GameStatistics:
    """Track and analyze statistics across multiple game runs."""

    def __init__(self):
        """Initialize statistics tracking."""
        self.total_games = 0
        # Track placements: bot_name -> list of placements (1 = winner, higher = earlier elimination)
        self.placements: Dict[str, List[int]] = defaultdict(list)
        # Track win counts
        self.wins: Dict[str, int] = defaultdict(int)
        # Track total participants
        self.total_bots = 0
        # Bot names
        self.bot_names: List[str] = []

    def record_game(self, results: List[tuple]) -> None:
        """
        Record results from a single game.
        
        Args:
            results: List of (bot_name, placement) tuples
                    placement 1 = winner (last alive)
                    placement 2 = second place (second to last eliminated)
                    etc.
        """
        self.total_games += 1
        
        for bot_name, placement in results:
            self.placements[bot_name].append(placement)
            if placement == 1:
                self.wins[bot_name] += 1
        
        # Update bot names if this is the first game
        if not self.bot_names:
            self.bot_names = [name for name, _ in results]
            self.total_bots = len(self.bot_names)

    def get_summary(self) -> Dict:
        """
        Get summary statistics.
        
        Returns:
            Dictionary containing summary statistics
        """
        if self.total_games == 0:
            return {}

        summary = {
            "total_games": self.total_games,
            "total_bots": self.total_bots,
            "bots": {}
        }

        for bot_name in self.bot_names:
            placements = self.placements[bot_name]
            wins = self.wins[bot_name]
            
            # Calculate placement counts
            placement_counts = {}
            for i in range(1, self.total_bots + 1):
                placement_counts[str(i)] = placements.count(i)
            
            # Calculate statistics
            avg_placement = sum(placements) / len(placements) if placements else 0
            win_rate = (wins / self.total_games * 100) if self.total_games > 0 else 0
            
            summary["bots"][bot_name] = {
                "wins": wins,
                "win_rate": round(win_rate, 2),
                "average_placement": round(avg_placement, 2),
                "placement_counts": placement_counts,
                "games_played": len(placements)
            }

        return summary

    def save_to_file(self, filename: str) -> None:
        """
        Save statistics to a JSON file.
        
        Args:
            filename: Path to the output file
        """
        summary = self.get_summary()
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)

    def print_summary(self) -> None:
        """Print a formatted summary of statistics to console."""
        if self.total_games == 0:
            print("No games recorded.")
            return

        print("\n" + "=" * 70)
        print(f"STATISTICS SUMMARY - {self.total_games} games played")
        print("=" * 70)
        
        # Sort bots by win rate (descending)
        sorted_bots = sorted(
            self.bot_names,
            key=lambda name: (self.wins[name], -sum(self.placements[name]) / len(self.placements[name])),
            reverse=True
        )
        
        for bot_name in sorted_bots:
            placements = self.placements[bot_name]
            wins = self.wins[bot_name]
            avg_placement = sum(placements) / len(placements)
            win_rate = (wins / self.total_games * 100)
            
            print(f"\n{bot_name}:")
            print(f"  Wins: {wins}/{self.total_games} ({win_rate:.1f}%)")
            print(f"  Average Placement: {avg_placement:.2f}")
            print(f"  Placement Distribution:")
            
            for i in range(1, self.total_bots + 1):
                count = placements.count(i)
                percentage = (count / self.total_games * 100) if self.total_games > 0 else 0
                bar_length = int(percentage / 2)  # Scale to fit in console
                bar = "█" * bar_length
                ordinal = self._get_ordinal(i)
                print(f"    {ordinal:6s}: {count:3d} ({percentage:5.1f}%) {bar}")
        
        print("\n" + "=" * 70)

    def _get_ordinal(self, n: int) -> str:
        """Convert number to ordinal string (1st, 2nd, 3rd, etc.)."""
        if 11 <= n <= 13:
            suffix = 'th'
        else:
            suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"
