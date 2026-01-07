"""
Dynamic bot loader for loading bots from a directory at runtime.

This module provides functionality to discover and load bot classes
from Python files in a specified directory.
"""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from game.bots.base import Bot

if TYPE_CHECKING:
    pass


class BotLoader:
    """
    Loads bot classes dynamically from a directory.
    
    The loader scans Python files in a directory for classes that
    inherit from Bot and instantiates them.
    """
    
    def __init__(self) -> None:
        """Initialize the bot loader."""
        self._loaded_bots: list[Bot] = []
    
    def load_from_directory(self, directory: str | Path) -> list[Bot]:
        """
        Load all bots from Python files in a directory.
        
        Each Python file is scanned for classes that inherit from Bot.
        For each such class found, an instance is created.
        
        Args:
            directory: Path to the directory containing bot files.
            
        Returns:
            List of instantiated bot objects.
            
        Raises:
            FileNotFoundError: If the directory doesn't exist.
        """
        dir_path: Path = Path(directory)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Bot directory not found: {directory}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory}")
        
        bots: list[Bot] = []
        
        # Find all Python files in the directory
        for py_file in dir_path.glob("*.py"):
            if py_file.name.startswith("_"):
                continue  # Skip __init__.py and private files
            
            file_bots: list[Bot] = self._load_bots_from_file(py_file)
            bots.extend(file_bots)
        
        self._loaded_bots = bots
        return bots
    
    def _load_bots_from_file(self, file_path: Path) -> list[Bot]:
        """
        Load bot classes from a single Python file.
        
        Args:
            file_path: Path to the Python file.
            
        Returns:
            List of instantiated bot objects from this file.
        """
        bots: list[Bot] = []
        
        # Create a unique module name
        module_name: str = f"loaded_bot_{file_path.stem}"
        
        # Load the module from file
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            print(f"Warning: Could not load module from {file_path}")
            return bots
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Warning: Error loading {file_path}: {e}")
            return bots
        
        # Find all Bot subclasses in the module
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # Check if it's a subclass of Bot but not Bot itself
            if issubclass(obj, Bot) and obj is not Bot:
                # Check if the class is defined in this module (not imported)
                if obj.__module__ == module_name:
                    try:
                        bot_instance: Bot = obj()
                        bots.append(bot_instance)
                        print(f"Loaded bot: {bot_instance.name} from {file_path.name}")
                    except Exception as e:
                        print(f"Warning: Could not instantiate {name}: {e}")
        
        return bots
    
    def load_from_file(self, file_path: str | Path) -> list[Bot]:
        """
        Load bots from a single Python file.
        
        Args:
            file_path: Path to the Python file.
            
        Returns:
            List of instantiated bot objects from the file.
        """
        path: Path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Bot file not found: {file_path}")
        
        bots: list[Bot] = self._load_bots_from_file(path)
        self._loaded_bots.extend(bots)
        return bots
    
    @property
    def loaded_bots(self) -> list[Bot]:
        """Get all currently loaded bots."""
        return self._loaded_bots
