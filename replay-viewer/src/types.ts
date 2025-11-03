/**
 * Type definitions for Exploding Kittens replay data
 */

export type CardType =
  | "EXPLODING_KITTEN"
  | "DEFUSE"
  | "SKIP"
  | "SEE_THE_FUTURE"
  | "SHUFFLE"
  | "ATTACK"
  | "FAVOR"
  | "NOPE"
  | "TACOCAT"
  | "CATTERMELON"
  | "HAIRY_POTATO_CAT"
  | "BEARD_CAT"
  | "RAINBOW_RALPHING_CAT";

export interface ReplayMetadata {
  timestamp: string;
  players: string[];
  version: string;
}

export interface GameSetupEvent {
  type: "game_setup";
  deck_size: number;
  initial_hand_size: number;
  play_order: string[];
  initial_hands: Record<string, CardType[]>;
}

export interface TurnStartEvent {
  type: "turn_start";
  turn_number: number;
  player: string;
  turns_remaining: number;
  hand_size: number;
  cards_in_deck: number;
}

export interface CardPlayEvent {
  type: "card_play";
  turn_number: number;
  player: string;
  card: CardType;
}

export interface ComboPlayEvent {
  type: "combo_play";
  turn_number: number;
  player: string;
  combo_type: string;
  cards: CardType[];
  target?: string;
}

export interface NopeEvent {
  type: "nope";
  turn_number: number;
  player: string;
  action: string;
}

export interface CardDrawEvent {
  type: "card_draw";
  turn_number: number;
  player: string;
  card: CardType;
}

export interface ExplodingKittenDrawEvent {
  type: "exploding_kitten_draw";
  turn_number: number;
  player: string;
  had_defuse: boolean;
}

export interface DefuseEvent {
  type: "defuse";
  turn_number: number;
  player: string;
  insert_position: number;
}

export interface PlayerEliminationEvent {
  type: "player_elimination";
  turn_number: number;
  player: string;
}

export interface SeeFutureEvent {
  type: "see_future";
  turn_number: number;
  player: string;
  cards_seen: number;
}

export interface ShuffleEvent {
  type: "shuffle";
  turn_number: number;
  player: string;
}

export interface FavorEvent {
  type: "favor";
  turn_number: number;
  player: string;
  target: string;
}

export interface CardStealEvent {
  type: "card_steal";
  turn_number: number;
  thief: string;
  victim: string;
  context: string;
}

export interface CardRequestEvent {
  type: "card_request";
  turn_number: number;
  requester: string;
  target: string;
  requested_card: CardType;
  success: boolean;
}

export interface DiscardTakeEvent {
  type: "discard_take";
  turn_number: number;
  player: string;
  card: CardType;
}

export interface GameEndEvent {
  type: "game_end";
  winner: string | null;
}

export type ReplayEvent =
  | GameSetupEvent
  | TurnStartEvent
  | CardPlayEvent
  | ComboPlayEvent
  | NopeEvent
  | CardDrawEvent
  | ExplodingKittenDrawEvent
  | DefuseEvent
  | PlayerEliminationEvent
  | SeeFutureEvent
  | ShuffleEvent
  | FavorEvent
  | CardStealEvent
  | CardRequestEvent
  | DiscardTakeEvent
  | GameEndEvent;

export interface ReplayData {
  metadata: ReplayMetadata;
  events: ReplayEvent[];
  winner: string | null;
}

export interface PlaybackState {
  currentEventIndex: number;
  isPlaying: boolean;
  speed: number; // events per second
  isPaused: boolean;
}
