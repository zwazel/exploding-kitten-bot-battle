"""Dynamic loading of bot classes from Python files."""

from __future__ import annotations

import importlib.util
import inspect
import sys
from pathlib import Path
from types import ModuleType
from typing import Type

from fastapi import HTTPException, status

from game import Bot


class BotLoadError(Exception):
    """Raised when a bot file cannot be loaded."""


def _load_module(path: Path, unique_name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(unique_name, path)
    if not spec or not spec.loader:
        raise BotLoadError(f"Unable to import bot module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def load_bot_class(path: Path, module_hint: str) -> Type[Bot]:
    module = _load_module(path, f"user_bot_{module_hint}")
    for _, obj in inspect.getmembers(module, inspect.isclass):
        if issubclass(obj, Bot) and obj is not Bot:
            return obj
    raise BotLoadError("No Bot subclass found in uploaded file")


def instantiate_bot(path: Path, module_hint: str, name: str) -> Bot:
    bot_class = load_bot_class(path, module_hint)
    return bot_class(name)


def require_bot(upload_path: Path, module_hint: str, name: str) -> Bot:
    try:
        return instantiate_bot(upload_path, module_hint, name)
    except BotLoadError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


__all__ = [
    "BotLoadError",
    "instantiate_bot",
    "require_bot",
]
