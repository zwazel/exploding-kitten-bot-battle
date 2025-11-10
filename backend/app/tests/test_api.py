from __future__ import annotations

import json
from typing import Dict

from fastapi.testclient import TestClient

from app.commands.setup_admin import main as setup_admin_main
from app.config import get_settings

BOT_CODE = """
from typing import Optional, List, Union
from game import Bot, GameState, Card, CardType, TargetContext, GameAction


class TestArenaBot(Bot):
    def play(self, state: GameState) -> Optional[Union[Card, List[Card]]]:
        return None

    def handle_exploding_kitten(self, state: GameState) -> int:
        return 0

    def see_the_future(self, state: GameState, top_three: List[Card]) -> None:
        return None

    def choose_target(self, state: GameState, alive_players: List[Bot], context: TargetContext) -> Optional[Bot]:
        return alive_players[0] if alive_players else None

    def choose_card_from_hand(self, state: GameState) -> Optional[Card]:
        return self.hand[0] if self.hand else None

    def choose_card_type(self, state: GameState) -> Optional[CardType]:
        return None

    def choose_from_discard(self, state: GameState, discard_pile: List[Card]) -> Optional[Card]:
        return discard_pile[-1] if discard_pile else None

    def on_action_played(self, state: GameState, action: GameAction, actor: Bot) -> None:
        return None

    def should_play_nope(self, state: GameState, action: GameAction) -> bool:
        return False
""".strip()


def _signup_payload(email: str) -> Dict[str, str]:
    return {
        "display_name": "TestUser",
        "email": email,
        "password": "supersecret",
    }


def test_signup_login_and_me(client: TestClient) -> None:
    response = client.post("/auth/signup", json=_signup_payload("user@example.com"))
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"
    assert body["username"] == "testuser"

    login_resp = client.post(
        "/auth/login",
        data={"username": "user@example.com", "password": "supersecret"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    me_resp = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "user@example.com"
    assert me_resp.json()["username"] == "testuser"


def test_bot_lifecycle(client: TestClient) -> None:
    # Seed admin bots to guarantee opponents
    settings = get_settings()
    bots_dir = settings.builtin_bots_directory
    setup_admin_main(
        [
            "--email",
            "admin@example.com",
            "--display-name",
            "AdminUser",
            "--password",
            "changeit",
            "--bots-dir",
            str(bots_dir),
        ]
    )

    email = "bot@example.com"
    client.post("/auth/signup", json=_signup_payload(email))
    login_resp = client.post(
        "/auth/login",
        data={"username": email, "password": "supersecret"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = login_resp.json()["access_token"]

    create_resp = client.post(
        "/bots",
        json={"name": "arena_bot"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201, create_resp.text
    bot_id = create_resp.json()["id"]

    list_resp = client.get("/bots", headers={"Authorization": f"Bearer {token}"})
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    upload_resp = client.post(
        f"/bots/{bot_id}/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("TestBot.py", BOT_CODE, "text/x-python")},
    )
    assert upload_resp.status_code == 200, upload_resp.text
    payload = upload_resp.json()
    assert payload["bot_version"]["version_number"] == 1
    replay_id = payload["replay"]["id"]
    assert replay_id > 0

    profile_resp = client.get(
        f"/bots/{bot_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_resp.status_code == 200
    profile = profile_resp.json()
    assert profile["current_version"]["version_number"] == 1
    assert profile["versions"][0]["is_active"] is True

    replay_resp = client.get(
        f"/replays/{replay_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert replay_resp.status_code == 200
    replay_body = replay_resp.json()
    assert replay_body["winner_name"]
    assert replay_body["participants"]

    file_resp = client.get(
        f"/replays/{replay_id}/file",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert file_resp.status_code == 200
    data = json.loads(file_resp.content)
    assert "events" in data

    delete_resp = client.delete(
        f"/bots/{bot_id}", headers={"Authorization": f"Bearer {token}"}
    )
    assert delete_resp.status_code == 204

    list_after_delete = client.get("/bots", headers={"Authorization": f"Bearer {token}"})
    assert list_after_delete.status_code == 200
    assert list_after_delete.json() == []
