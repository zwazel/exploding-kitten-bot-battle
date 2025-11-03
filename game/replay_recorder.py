"""Replay recording system for Exploding Kittens games."""

import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from .cards import Card, CardType


class ReplayRecorder:
    """
    Records game events for replay functionality.
    
    This class captures all important game actions in a structured format
    that can be used to replay the game visually later.
    """
    
    def __init__(self, player_names: List[str], enabled: bool = True):
        """
        Initialize the replay recorder.
        
        Args:
            player_names: List of player names in the game
            enabled: Whether recording is enabled
        """
        self.enabled = enabled
        self.events: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(),
            "players": player_names,
            "version": "1.0"
        }
        self.winner: Optional[str] = None
        self.turn_number = 0
    
    def record_game_setup(self, deck_size: int, initial_hand_size: int, 
                         play_order: List[str], 
                         initial_hands: Optional[Dict[str, List[str]]] = None) -> None:
        """Record initial game setup information."""
        if not self.enabled:
            return
        
        event = {
            "type": "game_setup",
            "deck_size": deck_size,
            "initial_hand_size": initial_hand_size,
            "play_order": play_order
        }
        
        if initial_hands:
            event["initial_hands"] = initial_hands
        
        self.events.append(event)
    
    def record_turn_start(self, player_name: str, turn_number: int, 
                         turns_remaining: int, hand_size: int, 
                         cards_in_deck: int) -> None:
        """Record the start of a player's turn."""
        if not self.enabled:
            return
        
        self.turn_number = turn_number
        self.events.append({
            "type": "turn_start",
            "turn_number": turn_number,
            "player": player_name,
            "turns_remaining": turns_remaining,
            "hand_size": hand_size,
            "cards_in_deck": cards_in_deck
        })
    
    def record_card_play(self, player_name: str, card_type: CardType) -> None:
        """Record a single card being played."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "card_play",
            "turn_number": self.turn_number,
            "player": player_name,
            "card": card_type.value
        })
    
    def record_combo_play(self, player_name: str, combo_type: str, 
                         cards: List[CardType], target: Optional[str] = None) -> None:
        """Record a combo being played."""
        if not self.enabled:
            return
        
        event: Dict[str, Any] = {
            "type": "combo_play",
            "turn_number": self.turn_number,
            "player": player_name,
            "combo_type": combo_type,
            "cards": [card.value for card in cards]
        }
        
        if target:
            event["target"] = target
        
        self.events.append(event)
    
    def record_nope(self, player_name: str, action_description: str) -> None:
        """Record a Nope card being played."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "nope",
            "turn_number": self.turn_number,
            "player": player_name,
            "action": action_description
        })
    
    def record_card_draw(self, player_name: str, card_type: CardType) -> None:
        """Record a card being drawn."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "card_draw",
            "turn_number": self.turn_number,
            "player": player_name,
            "card": card_type.value
        })
    
    def record_exploding_kitten_draw(self, player_name: str, 
                                    had_defuse: bool) -> None:
        """Record a player drawing an Exploding Kitten."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "exploding_kitten_draw",
            "turn_number": self.turn_number,
            "player": player_name,
            "had_defuse": had_defuse
        })
    
    def record_defuse(self, player_name: str, insert_position: int) -> None:
        """Record a player defusing an Exploding Kitten."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "defuse",
            "turn_number": self.turn_number,
            "player": player_name,
            "insert_position": insert_position
        })
    
    def record_player_elimination(self, player_name: str) -> None:
        """Record a player being eliminated."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "player_elimination",
            "turn_number": self.turn_number,
            "player": player_name
        })
    
    def record_see_future(self, player_name: str, num_cards: int) -> None:
        """Record a player using See the Future."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "see_future",
            "turn_number": self.turn_number,
            "player": player_name,
            "cards_seen": num_cards
        })
    
    def record_shuffle(self, player_name: str) -> None:
        """Record deck being shuffled."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "shuffle",
            "turn_number": self.turn_number,
            "player": player_name
        })
    
    def record_favor(self, player_name: str, target: str) -> None:
        """Record a Favor card being used."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "favor",
            "turn_number": self.turn_number,
            "player": player_name,
            "target": target
        })
    
    def record_card_steal(self, thief: str, victim: str, context: str) -> None:
        """Record a card being stolen (from combo or favor)."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "card_steal",
            "turn_number": self.turn_number,
            "thief": thief,
            "victim": victim,
            "context": context
        })
    
    def record_card_request(self, requester: str, target: str, 
                           card_type: CardType, success: bool) -> None:
        """Record a specific card being requested (3-of-a-kind)."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "card_request",
            "turn_number": self.turn_number,
            "requester": requester,
            "target": target,
            "requested_card": card_type.value,
            "success": success
        })
    
    def record_discard_take(self, player_name: str, card_type: CardType) -> None:
        """Record a card being taken from discard pile (5-unique)."""
        if not self.enabled:
            return
        
        self.events.append({
            "type": "discard_take",
            "turn_number": self.turn_number,
            "player": player_name,
            "card": card_type.value
        })
    
    def record_game_end(self, winner: Optional[str]) -> None:
        """Record the end of the game."""
        if not self.enabled:
            return
        
        self.winner = winner
        self.events.append({
            "type": "game_end",
            "winner": winner
        })
    
    def to_json(self) -> str:
        """
        Convert the recorded replay to JSON format.
        
        Returns:
            JSON string representation of the replay
        """
        replay_data = {
            "metadata": self.metadata,
            "events": self.events,
            "winner": self.winner
        }
        return json.dumps(replay_data, indent=2)
    
    def save_to_file(self, filepath: str) -> None:
        """
        Save the replay to a JSON file.
        
        Args:
            filepath: Path where to save the replay file
        """
        if not self.enabled:
            return
        
        with open(filepath, 'w') as f:
            f.write(self.to_json())
