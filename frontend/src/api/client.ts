import type { ReplayData } from "../types";
import type {
  ArenaMatchResponse,
  BotProfile,
  BotSummary,
  BotUploadResponse,
  TokenResponse,
  User,
} from "./types";

const metaEnv = (import.meta as unknown as { env?: Record<string, string | undefined> }).env ?? {};
const rawBaseUrl = metaEnv.VITE_API_BASE_URL || metaEnv.vite_api_base_url;
const API_BASE_URL = (rawBaseUrl ?? "http://localhost:8000").replace(/\/$/, "");

interface RequestOptions extends RequestInit {
  token?: string | null;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) {
      try {
        const data = await response.json();
        if (typeof data.detail === "string") {
          message = data.detail;
        }
      } catch {
        // ignore JSON parse failure
      }
    } else {
      const text = await response.text();
      if (text) {
        message = text;
      }
    }
    throw new Error(message);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return (await response.json()) as T;
  }

  return (await response.blob()) as T;
}

async function requestJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.token) {
    headers.set("Authorization", `Bearer ${options.token}`);
  }
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  });

  return handleResponse<T>(response);
}

export function getApiBaseUrl(): string {
  return API_BASE_URL;
}

export async function signup(payload: {
  email: string;
  password: string;
  display_name: string;
}): Promise<User> {
  return requestJson<User>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);
  return handleResponse<TokenResponse>(
    await fetch(`${API_BASE_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body,
    })
  );
}

export async function getCurrentUser(token: string): Promise<User> {
  return requestJson<User>("/auth/me", {
    method: "GET",
    token,
  });
}

export async function listBots(token: string): Promise<BotSummary[]> {
  return requestJson<BotSummary[]>("/bots", {
    method: "GET",
    token,
  });
}

export async function getBotProfile(token: string, botId: number): Promise<BotProfile> {
  return requestJson<BotProfile>(`/bots/${botId}`, {
    method: "GET",
    token,
  });
}

export async function uploadBot(token: string, file: File): Promise<BotUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return requestJson<BotUploadResponse>(`/bots/upload`, {
    method: "POST",
    body: formData,
    token,
  });
}

export async function startArenaMatch(token: string, botId: number): Promise<ArenaMatchResponse> {
  return requestJson<ArenaMatchResponse>(`/arena/matches`, {
    method: "POST",
    token,
    body: JSON.stringify({ bot_id: botId }),
  });
}

export async function deleteBot(token: string, botId: number): Promise<void> {
  return requestJson<void>(`/bots/${botId}`, {
    method: "DELETE",
    token,
  });
}

export async function fetchReplayMetadata(token: string, replayId: number): Promise<ReplayData> {
  return requestJson<ReplayData>(`/replays/${replayId}/file`, {
    method: "GET",
    token,
  });
}

export async function downloadReplayFile(token: string, replayId: number): Promise<Blob> {
  const response = await fetch(`${API_BASE_URL}/replays/${replayId}/file`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  if (!response.ok) {
    throw new Error(`Unable to download replay (${response.status})`);
  }
  return await response.blob();
}
