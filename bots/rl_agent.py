
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Any

from game.bots.base import Bot, Action, DrawCardAction, PlayCardAction, PlayComboAction, DefuseAction, GiveCardAction
from game.bots.view import BotView
from game.cards.base import Card
from game.history import GameEvent, EventType

# ==========================================
# 1. CONSTANTS & MAPPINGS
# ==========================================

CARD_TYPES = [
    "Nob", "NopeCard", "AttackCard", "SkipCard", "FavorCard", "ShuffleCard",
    "SeeTheFutureCard", "DefuseCard", "ExplodingKittenCard", "TacoCatCard",
    "HairyPotatoCatCard", "BeardCatCard", "RainbowRalphingCatCard", "CattermelonCard",
]
CARD_TYPE_TO_IDX = {name: i for i, name in enumerate(CARD_TYPES)}
NUM_CARD_TYPES = len(CARD_TYPES)

# ==========================================
# 2. MODELS (RLLSTM)
# ==========================================

class RLLSTM(nn.Module):
    def __init__(self, input_dim: int, num_actions: int, hidden_dim: int = 256, num_layers: int = 1):
        super().__init__()
        self.input_dim = input_dim
        self.num_actions = num_actions
        self.hidden_dim = hidden_dim
        
        self.fc_in = nn.Linear(input_dim, hidden_dim)
        self.lstm = nn.LSTM(hidden_dim, hidden_dim, num_layers=num_layers, batch_first=True)
        
        self.actor_turn = nn.Linear(hidden_dim, num_actions)
        self.actor_reaction = nn.Linear(hidden_dim, num_actions)
        self.actor_defuse = nn.Linear(hidden_dim, 2)
        self.actor_give = nn.Linear(hidden_dim, 14)
        self.critic = nn.Linear(hidden_dim, 1)

    def forward(self, x, h=None):
        x = F.relu(self.fc_in(x))
        out, h_new = self.lstm(x, h)
        return {
            "turn": self.actor_turn(out),
            "reaction": self.actor_reaction(out),
            "defuse": self.actor_defuse(out),
            "give": self.actor_give(out),
            "value": self.critic(out)
        }, h_new

# ==========================================
# 3. AGENT WRAPPER
# ==========================================

class Agent:
    def __init__(self, input_dim: int, num_actions: int, device="cpu"):
        self.device = device
        self.model = RLLSTM(input_dim, num_actions).to(device)
        self.hidden = None
    
    def reset(self):
        self.hidden = None

    def load(self, path: str):
        # Map location ensures we can load on CPU if trained on CUDA
        self.model.load_state_dict(torch.load(path, map_location=self.device))
        
    def select_action(self, obs: np.ndarray, mask: np.ndarray, mode: str = "turn", deterministic: bool = False) -> int:
        self.model.eval()
        with torch.no_grad():
            x = torch.FloatTensor(obs).unsqueeze(0).unsqueeze(0).to(self.device)
            out, self.hidden = self.model(x, self.hidden)
            
            if mode == "turn": logits = out["turn"]
            elif mode == "reaction": logits = out["reaction"]
            elif mode == "defuse": return torch.argmax(out["defuse"]).item()
            elif mode == "give_card": return torch.argmax(out["give"]).item()
            else: return 0

            logits = logits[0, 0]
            if mask is not None:
                mask_t = torch.BoolTensor(mask).to(self.device)
                logits[~mask_t] = -1e9
            
            if deterministic:
                return torch.argmax(logits).item()
            else:
                probs = torch.softmax(logits, dim=0)
                return torch.multinomial(probs, 1).item()

# ==========================================
# 4. STATE ENCODER
# ==========================================

class StateEncoder:
    def __init__(self, history_len=5):
        self.history_len = history_len
        self.max_opponents = 4
        self.actions = []
        self._build_action_space()
        self.num_actions = len(self.actions)

    def _build_action_space(self):
        self.actions = []
        self.actions.append(("PASS", None, None))
        self.actions.append(("DRAW", None, None))
        
        simple_singles = ["AttackCard", "SkipCard", "ShuffleCard", "SeeTheFutureCard"]
        for ct in simple_singles:
            self.actions.append(("PLAY_SINGLE", ct, None))
            
        self.actions.append(("PLAY_NOPE", "NopeCard", None))
            
        for i in range(self.max_opponents):
            self.actions.append(("PLAY_FAVOR", "FavorCard", i))
            
        combo_types = [
            "TacoCatCard", "HairyPotatoCatCard", "BeardCatCard", 
            "RainbowRalphingCatCard", "CattermelonCard",
            "AttackCard", "SkipCard", "ShuffleCard", "SeeTheFutureCard", "FavorCard"
        ]
        for ct in combo_types:
            for i in range(self.max_opponents):
                self.actions.append(("PLAY_PAIR", ct, i))

    def encode_state(self, view: BotView) -> dict[str, np.ndarray]:
        hand_counts = np.zeros(NUM_CARD_TYPES, dtype=np.float32)
        for card in view.my_hand:
            if card.card_type in CARD_TYPE_TO_IDX:
                hand_counts[CARD_TYPE_TO_IDX[card.card_type]] += 1
                
        public_state = np.zeros(4, dtype=np.float32)
        public_state[0] = view.draw_pile_count / 50.0 
        public_state[1] = view.my_turns_remaining
        public_state[2] = len(view.other_players)
        
        discard_encoding = np.zeros(NUM_CARD_TYPES, dtype=np.float32)
        if view.discard_pile:
            top_card = view.discard_pile[-1]
            if top_card.card_type in CARD_TYPE_TO_IDX:
                discard_encoding[CARD_TYPE_TO_IDX[top_card.card_type]] = 1.0
                
        opp_state = np.zeros((self.max_opponents, 2), dtype=np.float32)
        for i, pid in enumerate(view.other_players):
            if i >= self.max_opponents: break
            count = view.other_player_card_counts.get(pid, 0)
            opp_state[i, 0] = count / 10.0
            opp_state[i, 1] = 1.0
            
        flat_obs = np.concatenate([
            hand_counts, public_state, discard_encoding, opp_state.flatten()
        ])
        
        return {"obs": flat_obs}

    def get_legal_actions(self, view: BotView, mode: str = "turn") -> np.ndarray:
        mask = np.zeros(self.num_actions, dtype=bool)
        if mode == "reaction":
            mask[0] = True # PASS
            # Nope logic
            nope_idx = -1
            for i, act in enumerate(self.actions):
                if act[0] == "PLAY_NOPE": nope_idx = i; break
            if view.has_card_type("NopeCard"):
                mask[nope_idx] = True
            return mask
        elif mode == "turn":
            mask[1] = True # DRAW
            for i, (atype, ctype, target_idx) in enumerate(self.actions):
                if atype == "PLAY_SINGLE":
                    if view.has_card_type(ctype): mask[i] = True
                elif atype == "PLAY_FAVOR":
                    if view.has_card_type("FavorCard") and target_idx < len(view.other_players):
                         mask[i] = True
                elif atype == "PLAY_PAIR":
                     if view.count_cards_of_type(ctype) >= 2 and target_idx < len(view.other_players):
                         mask[i] = True
            if view.has_card_type("NopeCard"):
                for i, act in enumerate(self.actions):
                    if act[0] == "PLAY_NOPE": mask[i] = True
            return mask
        return mask

    def decode_action(self, action_idx: int, view: BotView) -> Action:
        if action_idx < 0 or action_idx >= self.num_actions: return DrawCardAction()
        atype, ctype, target_idx = self.actions[action_idx]
        
        if atype == "PASS": return None
        if atype == "DRAW": return DrawCardAction()
        
        target_pid = None
        if target_idx is not None:
             if target_idx < len(view.other_players):
                 target_pid = view.other_players[target_idx]
             elif view.other_players:
                 target_pid = view.other_players[0]
             else:
                 return DrawCardAction()
        
        if atype in ["PLAY_SINGLE", "PLAY_FAVOR", "PLAY_NOPE"]:
            cards = view.get_cards_of_type(ctype)
            if not cards: return DrawCardAction()
            return PlayCardAction(card=cards[0], target_player_id=target_pid)
            
        if atype == "PLAY_PAIR":
            cards = view.get_cards_of_type(ctype)
            if len(cards) < 2: return DrawCardAction()
            return PlayComboAction(cards=cards[:2], target_player_id=target_pid)
        return DrawCardAction()
        
    def decode_defuse(self, action_idx: int, view: BotView, pile_size: int) -> int:
        return 0 if action_idx == 0 else pile_size
        
    def decode_give_card(self, action_idx: int, view: BotView) -> Card:
        if 0 <= action_idx < len(CARD_TYPES):
            cards = view.get_cards_of_type(CARD_TYPES[action_idx])
            if cards: return cards[0]
        if view.my_hand: return view.my_hand[0]
        # Should raise error but safe fallback to random logic handled by engine usually
        return view.my_hand[0]

# ==========================================
# 5. THE BOT
# ==========================================

class TrainedBot(Bot):
    """
    Self-contained RL Bot for Exploding Kittens.
    """
    def __init__(self):
        self._name = "RL_Final"
        self.device = "cpu"
        self.encoder = StateEncoder()
        
        # Initialize Agent
        input_dim = 40
        num_actions = self.encoder.num_actions
        self.agent = Agent(input_dim, num_actions, device=self.device)
        
        # Load Model (Dynamically find checkpoint same folder as this file)
        # Assumes 'model_latest.pt' is in the same directory as this bot file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(current_dir, "model_latest.pt")
        
        if os.path.exists(model_path):
            try:
                self.agent.load(model_path)
                print(f"RL_Final loaded model from {model_path}")
            except Exception as e:
                print(f"RL_Final ERROR: Could not load model: {e}")
        else:
            print(f"RL_Final WARNING: No model found at {model_path}. Playing randomly.")

    @property
    def name(self) -> str:
        return self._name

    def take_turn(self, view: BotView) -> Action:
        state_dict = self.encoder.encode_state(view)
        mask = self.encoder.get_legal_actions(view, mode="turn")
        idx = self.agent.select_action(state_dict["obs"], mask, mode="turn", deterministic=True)
        return self.encoder.decode_action(idx, view)

    def react(self, view: BotView, triggering_event) -> Action | None:
        state_dict = self.encoder.encode_state(view)
        mask = self.encoder.get_legal_actions(view, mode="reaction")
        idx = self.agent.select_action(state_dict["obs"], mask, mode="reaction", deterministic=True)
        if idx == 0: return None
        return self.encoder.decode_action(idx, view)

    def choose_defuse_position(self, view: BotView, draw_pile_size: int) -> int:
        state_dict = self.encoder.encode_state(view)
        idx = self.agent.select_action(state_dict["obs"], None, mode="defuse", deterministic=True)
        return self.encoder.decode_defuse(idx, view, draw_pile_size)

    def choose_card_to_give(self, view: BotView, requester_id: str) -> Card:
        state_dict = self.encoder.encode_state(view)
        idx = self.agent.select_action(state_dict["obs"], None, mode="give_card", deterministic=True)
        return self.encoder.decode_give_card(idx, view)

    def on_explode(self, view: BotView) -> None: pass
    def on_event(self, event, view): pass

