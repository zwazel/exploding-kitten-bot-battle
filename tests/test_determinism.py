"""
Tests for deterministic RNG behavior.

These tests verify that using the same seed produces identical
game outcomes, which is crucial for debugging and replay.
"""

import pytest

from game.rng import DeterministicRNG


class TestDeterministicRNG:
    """Tests for the DeterministicRNG class."""
    
    def test_same_seed_produces_same_sequence(self) -> None:
        """The same seed should produce identical random sequences."""
        rng1: DeterministicRNG = DeterministicRNG(seed=42)
        rng2: DeterministicRNG = DeterministicRNG(seed=42)
        
        # Generate sequences from both
        seq1: list[int] = [rng1.randint(0, 100) for _ in range(10)]
        seq2: list[int] = [rng2.randint(0, 100) for _ in range(10)]
        
        assert seq1 == seq2
    
    def test_different_seeds_produce_different_sequences(self) -> None:
        """Different seeds should produce different sequences."""
        rng1: DeterministicRNG = DeterministicRNG(seed=42)
        rng2: DeterministicRNG = DeterministicRNG(seed=123)
        
        seq1: list[int] = [rng1.randint(0, 100) for _ in range(10)]
        seq2: list[int] = [rng2.randint(0, 100) for _ in range(10)]
        
        assert seq1 != seq2
    
    def test_shuffle_is_deterministic(self) -> None:
        """Shuffling with the same seed should produce same order."""
        rng1: DeterministicRNG = DeterministicRNG(seed=42)
        rng2: DeterministicRNG = DeterministicRNG(seed=42)
        
        list1: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        list2: list[int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        rng1.shuffle(list1)
        rng2.shuffle(list2)
        
        assert list1 == list2
    
    def test_choice_is_deterministic(self) -> None:
        """Choice with the same seed should produce same results."""
        rng1: DeterministicRNG = DeterministicRNG(seed=42)
        rng2: DeterministicRNG = DeterministicRNG(seed=42)
        
        items: list[str] = ["a", "b", "c", "d", "e"]
        
        choices1: list[str] = [rng1.choice(items) for _ in range(10)]
        choices2: list[str] = [rng2.choice(items) for _ in range(10)]
        
        assert choices1 == choices2
    
    def test_sample_is_deterministic(self) -> None:
        """Sample with the same seed should produce same results."""
        rng1: DeterministicRNG = DeterministicRNG(seed=42)
        rng2: DeterministicRNG = DeterministicRNG(seed=42)
        
        items: list[int] = list(range(20))
        
        sample1: list[int] = rng1.sample(items, 5)
        sample2: list[int] = rng2.sample(items, 5)
        
        assert sample1 == sample2
    
    def test_seed_property(self) -> None:
        """The seed property should return the original seed."""
        rng: DeterministicRNG = DeterministicRNG(seed=12345)
        assert rng.seed == 12345
