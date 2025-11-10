"""Pydantic schemas for request and response bodies."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserBase(BaseModel):
    email: EmailStr
    display_name: str


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserPublic(UserBase):
    id: int
    username: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotVersionSummary(BaseModel):
    id: int
    version_number: int
    created_at: datetime
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ReplayParticipantSummary(BaseModel):
    bot_label: str
    placement: int
    is_winner: bool


class ReplaySummary(BaseModel):
    id: int
    created_at: datetime
    winner_name: str
    participants: list[ReplayParticipantSummary]
    summary: dict

    model_config = ConfigDict(from_attributes=True)


class BotSummary(BaseModel):
    id: int
    name: str
    qualified_name: str
    created_at: datetime
    current_version: Optional[BotVersionSummary]

    model_config = ConfigDict(from_attributes=True)


class BotProfile(BaseModel):
    id: int
    name: str
    qualified_name: str
    created_at: datetime
    current_version: Optional[BotVersionSummary]
    versions: list[BotVersionSummary]
    recent_replays: list[ReplaySummary]


class BotCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UploadResponse(BaseModel):
    bot_version: BotVersionSummary
    replay: ReplaySummary


__all__ = [
    "TokenResponse",
    "UserCreate",
    "UserPublic",
    "BotSummary",
    "BotProfile",
    "BotCreateRequest",
    "LoginRequest",
    "UploadResponse",
    "BotVersionSummary",
    "ReplaySummary",
    "ReplayParticipantSummary",
]
