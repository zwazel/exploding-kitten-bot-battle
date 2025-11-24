"""Synchronise admin-owned bots from the local bots directory."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

from sqlalchemy.orm import Session

from .. import models
from ..auth import hash_password
from ..database import session_scope
from ..services.bot_loader import require_bot
from ..services.bot_versions import compute_file_hash
from ..services.storage import StorageManager
from ..utils import clean_identifier, enforce_bot_name, make_qualified_bot_name


def _ensure_admin(
    session: Session,
    email: str,
    display_name: str,
    password: str,
) -> models.User:
    username = clean_identifier(display_name)
    user = session.query(models.User).filter(models.User.email == email).first()
    conflict = (
        session.query(models.User)
        .filter(models.User.username == username)
        .filter(models.User.email != email)
        .first()
    )
    if conflict:
        raise SystemExit(
            f"Username {username} already exists for another user; choose a different display name"
        )
    hashed_password = hash_password(password)
    if user:
        user.display_name = display_name
        user.username = username
        user.password_hash = hashed_password
        session.add(user)
    else:
        user = models.User(
            email=email,
            username=username,
            display_name=display_name,
            password_hash=hashed_password,
        )
        session.add(user)
        session.flush()
    return user


def _sync_bot(
    session: Session,
    storage: StorageManager,
    user: models.User,
    source: Path,
) -> None:
    bot_name = enforce_bot_name(source.stem)
    bot = (
        session.query(models.Bot)
        .filter(models.Bot.user_id == user.id)
        .filter(models.Bot.name == bot_name)
        .first()
    )
    if not bot:
        bot = models.Bot(user_id=user.id, name=bot_name)
        bot.owner = user
        session.add(bot)
        session.flush()

    file_hash = compute_file_hash(source)
    existing_version = next(
        (version for version in bot.versions if version.file_hash == file_hash),
        None,
    )

    if existing_version:
        current_path = Path(existing_version.file_path or "")
        if not current_path.exists():
            destination = storage.copy_bot_file(
                user.id, bot.id, existing_version.version_number, source
            )
            existing_version.file_path = str(destination)
            session.add(existing_version)
        bot.current_version_id = existing_version.id
        session.add(bot)
        return

    next_version = (
        max((version.version_number for version in bot.versions), default=0) + 1
    )
    destination = storage.copy_bot_file(user.id, bot.id, next_version, source)

    label = make_qualified_bot_name(user.username, bot.name)
    require_bot(destination, f"admin_{user.id}_{bot.id}_{next_version}", label)

    version = models.BotVersion(
        bot_id=bot.id,
        version_number=next_version,
        file_path=str(destination),
        file_hash=file_hash,
    )
    session.add(version)
    session.flush()

    bot.current_version_id = version.id
    session.add(bot)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Sync admin bots from a directory")
    parser.add_argument("--email", required=True, help="Admin email address")
    parser.add_argument("--display-name", required=True, help="Admin display name/username")
    parser.add_argument("--password", help="Admin password; defaults to ARENA_ADMIN_PASSWORD env var")
    parser.add_argument(
        "--bots-dir",
        default=str(Path.cwd() / "bots"),
        help="Directory containing bot python files",
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    password = args.password or os.environ.get("ARENA_ADMIN_PASSWORD")
    if not password:
        raise SystemExit("An admin password must be provided via --password or ARENA_ADMIN_PASSWORD")

    bots_dir = Path(args.bots_dir)
    if not bots_dir.exists() or not bots_dir.is_dir():
        raise SystemExit(f"Bots directory {bots_dir} does not exist")

    storage = StorageManager()

    with session_scope() as session:
        user = _ensure_admin(session, args.email.lower(), args.display_name, password)
        for path in sorted(bots_dir.glob("*.py")):
            if path.name.startswith("__"):
                continue
            _sync_bot(session, storage, user, path)


if __name__ == "__main__":
    main()
