"""Helpers for consistent bot and user naming rules."""

from __future__ import annotations

import re

BOT_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def clean_identifier(value: str) -> str:
    """Normalise a string into a lowercase identifier with limited characters."""

    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip())
    cleaned = re.sub(r"_+", "_", cleaned)
    cleaned = cleaned.strip("_")
    if not cleaned:
        raise ValueError("Identifier cannot be empty after cleaning")
    return cleaned.lower()


def enforce_bot_name(name: str) -> str:
    """Validate bot names to ensure they conform to the required pattern."""

    if not BOT_NAME_PATTERN.fullmatch(name):
        raise ValueError("Bot names may only contain letters, numbers, underscores, and hyphens")
    return name.lower()


def make_qualified_bot_name(username: str, bot_name: str) -> str:
    """Generate the globally unique bot label from a username and bot name."""

    user_identifier = clean_identifier(username)
    bot_identifier = enforce_bot_name(bot_name)
    return f"{user_identifier}_{bot_identifier}"


__all__ = [
    "BOT_NAME_PATTERN",
    "clean_identifier",
    "enforce_bot_name",
    "make_qualified_bot_name",
]
