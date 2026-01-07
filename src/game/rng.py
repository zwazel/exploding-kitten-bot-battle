"""
Deterministic random number generator for reproducible games.

All game randomness must go through this class to ensure reproducibility
when the same seed is used.
"""

import random
from typing import TypeVar

T = TypeVar("T")


class DeterministicRNG:
    """
    A wrapper around Python's random module that ensures deterministic behavior.
    
    All random operations in the game should use this class to guarantee
    that the same seed produces the same game outcomes.
    
    Attributes:
        seed: The seed used to initialize the RNG.
    """
    
    def __init__(self, seed: int) -> None:
        """
        Initialize the RNG with a specific seed.
        
        Args:
            seed: The seed value for reproducible randomness.
        """
        self._seed: int = seed
        self._random: random.Random = random.Random(seed)
    
    @property
    def seed(self) -> int:
        """Get the original seed used to initialize this RNG."""
        return self._seed
    
    def shuffle(self, items: list[T]) -> None:
        """
        Shuffle a list in place.
        
        Args:
            items: The list to shuffle. Modified in place.
        """
        self._random.shuffle(items)
    
    def choice(self, items: list[T]) -> T:
        """
        Return a random element from a non-empty list.
        
        Args:
            items: The list to choose from.
            
        Returns:
            A randomly selected element.
            
        Raises:
            IndexError: If the list is empty.
        """
        return self._random.choice(items)
    
    def randint(self, a: int, b: int) -> int:
        """
        Return a random integer N such that a <= N <= b.
        
        Args:
            a: Lower bound (inclusive).
            b: Upper bound (inclusive).
            
        Returns:
            A random integer in the range [a, b].
        """
        return self._random.randint(a, b)
    
    def random(self) -> float:
        """
        Return a random float in the range [0.0, 1.0).
        
        Returns:
            A random float.
        """
        return self._random.random()
    
    def sample(self, items: list[T], k: int) -> list[T]:
        """
        Return k unique random elements from a list.
        
        Args:
            items: The list to sample from.
            k: Number of elements to sample.
            
        Returns:
            A new list containing k randomly selected elements.
            
        Raises:
            ValueError: If k is larger than the list length.
        """
        return self._random.sample(items, k)
