from __future__ import annotations

import json
from typing import Dict

from fastapi.testclient import TestClient

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
        "display_name": "Test User",
        "email": email,
        "password": "supersecret",
    }


def test_signup_login_and_me(client: TestClient) -> None:
    response = client.post("/auth/signup", json=_signup_payload("user@example.com"))
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "user@example.com"

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


def test_upload_bot_and_fetch_replay(client: TestClient) -> None:
    email = "bot@example.com"
    client.post("/auth/signup", json=_signup_payload(email))
    login_resp = client.post(
        "/auth/login",
        data={"username": email, "password": "supersecret"},
        headers={"content-type": "application/x-www-form-urlencoded"},
    )
    token = login_resp.json()["access_token"]

    upload_resp = client.post(
        "/bots/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("TestBot.py", BOT_CODE, "text/x-python")},
    )
    assert upload_resp.status_code == 200, upload_resp.text
    payload = upload_resp.json()
    assert payload["bot_version"]["version_number"] == 1
    replay_id = payload["replay"]["id"]
    assert replay_id > 0

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
