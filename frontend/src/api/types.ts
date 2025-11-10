export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface User {
  id: number;
  email: string;
  display_name: string;
  created_at: string;
}

export interface BotVersionSummary {
  id: number;
  version_number: number;
  created_at: string;
  is_active: boolean;
}

export interface ReplayParticipantSummary {
  bot_label: string;
  placement: number;
  is_winner: boolean;
}

export interface ReplaySummary {
  id: number;
  created_at: string;
  winner_name: string;
  participants: ReplayParticipantSummary[];
  summary: Record<string, unknown>;
}

export interface BotProfile {
  bot_id: number;
  current_version: BotVersionSummary | null;
  versions: BotVersionSummary[];
  recent_replays: ReplaySummary[];
}

export interface UploadResponse {
  bot_version: BotVersionSummary;
  replay: ReplaySummary;
}
