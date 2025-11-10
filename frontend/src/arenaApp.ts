import {
  downloadReplayFile,
  fetchReplayMetadata,
  getApiBaseUrl,
  getBotProfile,
  getCurrentUser,
  login,
  signup,
  uploadBotFile,
} from "./api/client";
import type { BotProfile, ReplaySummary, User } from "./api/types";
import { ReplayApp } from "./replayApp";

const TOKEN_STORAGE_KEY = "exploding-kitten-arena-token";

function formatDate(timestamp: string): string {
  try {
    return new Date(timestamp).toLocaleString();
  } catch {
    return timestamp;
  }
}

function summarizeReplay(summary: ReplaySummary): string {
  const placements = summary.participants
    .map((p) => `${p.placement}. ${p.bot_label}${p.is_winner ? " 🏆" : ""}`)
    .join(" | ");
  return `${formatDate(summary.created_at)} · Winner: ${summary.winner_name} · ${placements}`;
}

interface ArenaOptions {
  onShowReplay?: () => void;
}

export class ArenaApp {
  private readonly root: HTMLElement;
  private readonly replayApp: ReplayApp;
  private readonly onShowReplay?: () => void;
  private token: string | null = null;
  private user: User | null = null;
  private profile: BotProfile | null = null;

  constructor(root: HTMLElement, replayApp: ReplayApp, options: ArenaOptions = {}) {
    this.root = root;
    this.replayApp = replayApp;
    this.onShowReplay = options.onShowReplay;
    this.renderBaseLayout();
    this.restoreToken();
    this.attachAuthHandlers();
    this.attachUploadHandler();
    this.attachReplayHandlers();
  }

  private renderBaseLayout(): void {
    this.root.innerHTML = `
      <div class="arena">
        <div class="auth-panels" data-view="logged-out">
          <div class="auth-card">
            <h2>Log in</h2>
            <form id="login-form" class="form-stack">
              <label>Email<input type="email" name="email" required autocomplete="email" /></label>
              <label>Password<input type="password" name="password" required autocomplete="current-password" /></label>
              <button type="submit" class="primary-button">Log in</button>
            </form>
            <p class="form-feedback" id="login-feedback"></p>
          </div>
          <div class="auth-card">
            <h2>Sign up</h2>
            <form id="signup-form" class="form-stack">
              <label>Display name<input type="text" name="display_name" required autocomplete="nickname" /></label>
              <label>Email<input type="email" name="email" required autocomplete="email" /></label>
              <label>Password<input type="password" name="password" minlength="8" required autocomplete="new-password" /></label>
              <button type="submit" class="secondary-button">Create account</button>
            </form>
            <p class="form-feedback" id="signup-feedback"></p>
          </div>
        </div>
        <div class="arena-dashboard hidden" data-view="logged-in">
          <div class="dashboard-header">
            <div>
              <h2 id="arena-user-info"></h2>
              <p class="subtle" id="arena-api-info"></p>
            </div>
            <button id="logout-button" class="secondary-button">Log out</button>
          </div>

          <section class="card upload-card">
            <h3>Upload a new bot</h3>
            <form id="upload-form" class="upload-form">
              <input type="file" id="bot-file" name="bot" accept=".py" required />
              <button type="submit" class="primary-button">Upload &amp; run arena match</button>
            </form>
            <p class="subtle">Uploading a new file replaces your previous bot. The arena will immediately run a match and record the replay.</p>
            <p class="form-feedback" id="upload-feedback"></p>
          </section>

          <section class="card" id="current-bot-card">
            <h3>Your bot</h3>
            <div id="current-bot"></div>
          </section>

          <section class="card">
            <h3>Bot versions</h3>
            <ul id="bot-versions" class="simple-list"></ul>
          </section>

          <section class="card">
            <h3>Recent arena replays</h3>
            <ul id="replay-list" class="replay-list"></ul>
          </section>
        </div>
      </div>
    `;
  }

  private restoreToken(): void {
    const stored = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (stored) {
      this.token = stored;
      this.bootstrapProfile();
    } else {
      this.showAuthPanels();
    }
  }

  private async bootstrapProfile(): Promise<void> {
    if (!this.token) return;
    try {
      this.user = await getCurrentUser(this.token);
      this.profile = await getBotProfile(this.token);
      this.updateDashboard();
      this.showDashboard();
    } catch (error) {
      console.error("Failed to restore session", error);
      this.setFeedback("login-feedback", "Unable to restore session. Please log in again.", false);
      this.clearToken();
      this.showAuthPanels();
    }
  }

  private attachAuthHandlers(): void {
    const loginForm = this.root.querySelector<HTMLFormElement>("#login-form");
    const signupForm = this.root.querySelector<HTMLFormElement>("#signup-form");
    const logoutButton = this.root.querySelector<HTMLButtonElement>("#logout-button");

    loginForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(loginForm);
      const email = (formData.get("email") as string).trim();
      const password = (formData.get("password") as string).trim();
      try {
        this.setFeedback("login-feedback", "Logging in…", true);
        const token = await login(email, password);
        this.saveToken(token.access_token);
        await this.bootstrapProfile();
        this.setFeedback("login-feedback", "", true);
      } catch (error) {
        this.setFeedback("login-feedback", (error as Error).message, false);
      }
    });

    signupForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      const formData = new FormData(signupForm);
      const payload = {
        display_name: (formData.get("display_name") as string).trim(),
        email: (formData.get("email") as string).trim(),
        password: (formData.get("password") as string).trim(),
      };
      try {
        this.setFeedback("signup-feedback", "Creating account…", true);
        await signup(payload);
        const token = await login(payload.email, payload.password);
        this.saveToken(token.access_token);
        await this.bootstrapProfile();
        this.setFeedback("signup-feedback", "Welcome! Your account is ready.", true);
      } catch (error) {
        this.setFeedback("signup-feedback", (error as Error).message, false);
      }
    });

    logoutButton?.addEventListener("click", () => {
      this.clearToken();
      this.user = null;
      this.profile = null;
      this.showAuthPanels();
    });
  }

  private attachUploadHandler(): void {
    const uploadForm = this.root.querySelector<HTMLFormElement>("#upload-form");
    if (!uploadForm) return;

    uploadForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!this.token) {
        this.setFeedback("upload-feedback", "Log in to upload a bot.", false);
        return;
      }
      const fileInput = this.root.querySelector<HTMLInputElement>("#bot-file");
      const file = fileInput?.files?.[0];
      if (!file) {
        this.setFeedback("upload-feedback", "Select a Python file to upload.", false);
        return;
      }
      try {
        this.setFeedback("upload-feedback", "Uploading and running match…", true);
        const result = await uploadBotFile(this.token, file);
        const summaryPlacements = (result.replay.summary as Record<string, unknown>).placements;
        let placementText = "Match completed.";
        if (Array.isArray(summaryPlacements)) {
          const entries = summaryPlacements
            .filter((entry): entry is [string, number] => Array.isArray(entry) && entry.length === 2)
            .map(([name, place]) => `${place}. ${name}`);
          if (entries.length) {
            placementText = entries.join(" | ");
          }
        }
        this.setFeedback(
          "upload-feedback",
          `Match finished. Winner: ${result.replay.winner_name}. Placements: ${placementText}.`,
          true
        );
        await this.bootstrapProfile();
      } catch (error) {
        this.setFeedback("upload-feedback", (error as Error).message, false);
      } finally {
        uploadForm.reset();
      }
    });
  }

  private attachReplayHandlers(): void {
    const replayList = this.root.querySelector<HTMLUListElement>("#replay-list");
    replayList?.addEventListener("click", async (event) => {
      const target = event.target as HTMLElement;
      const action = target.getAttribute("data-action");
      const idValue = target.getAttribute("data-replay-id");
      if (!action || !idValue) return;
      const replayId = Number.parseInt(idValue, 10);
      if (Number.isNaN(replayId) || !this.token) return;

      if (action === "view") {
        await this.viewReplay(replayId, target);
      } else if (action === "download") {
        await this.downloadReplay(replayId, target);
      }
    });
  }

  private async viewReplay(replayId: number, target: HTMLElement): Promise<void> {
    try {
      target.setAttribute("disabled", "true");
      const replayData = await fetchReplayMetadata(this.token!, replayId);
      await this.replayApp.loadReplayFromData(replayData, `Arena replay #${replayId}`);
      this.onShowReplay?.();
      this.setFeedback("upload-feedback", "Replay loaded in the viewer.", true);
    } catch (error) {
      this.setFeedback("upload-feedback", (error as Error).message, false);
    } finally {
      target.removeAttribute("disabled");
    }
  }

  private async downloadReplay(replayId: number, target: HTMLElement): Promise<void> {
    try {
      target.setAttribute("disabled", "true");
      const blob = await downloadReplayFile(this.token!, replayId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `replay-${replayId}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (error) {
      this.setFeedback("upload-feedback", (error as Error).message, false);
    } finally {
      target.removeAttribute("disabled");
    }
  }

  private updateDashboard(): void {
    const dashboard = this.root.querySelector<HTMLDivElement>(".arena-dashboard");
    if (!dashboard) return;
    const info = dashboard.querySelector<HTMLHeadingElement>("#arena-user-info");
    const apiInfo = dashboard.querySelector<HTMLParagraphElement>("#arena-api-info");
    const currentBotContainer = dashboard.querySelector<HTMLDivElement>("#current-bot");
    const versionsList = dashboard.querySelector<HTMLUListElement>("#bot-versions");
    const replayList = dashboard.querySelector<HTMLUListElement>("#replay-list");

    if (info && this.user) {
      info.textContent = `${this.user.display_name} (${this.user.email})`;
    }
    if (apiInfo) {
      apiInfo.textContent = `API base: ${getApiBaseUrl()}`;
    }

    if (currentBotContainer) {
      if (this.profile?.current_version) {
        const v = this.profile.current_version;
        currentBotContainer.innerHTML = `<p>Active version <strong>${v.version_number}</strong> uploaded ${formatDate(v.created_at)}.</p>`;
      } else {
        currentBotContainer.innerHTML = `<p>No bot uploaded yet. Upload a Python bot file to enter the arena.</p>`;
      }
    }

    if (versionsList) {
      versionsList.innerHTML = "";
      this.profile?.versions.forEach((version) => {
        const li = document.createElement("li");
        li.textContent = `${version.version_number}. uploaded ${formatDate(version.created_at)}${version.is_active ? " (active)" : ""}`;
        versionsList.appendChild(li);
      });
      if (!versionsList.hasChildNodes()) {
        const li = document.createElement("li");
        li.textContent = "No versions yet.";
        versionsList.appendChild(li);
      }
    }

    if (replayList) {
      replayList.innerHTML = "";
      this.profile?.recent_replays.forEach((replay) => {
        const li = document.createElement("li");
        li.innerHTML = `
          <div class="replay-entry">
            <div>
              <p>${summarizeReplay(replay)}</p>
            </div>
            <div class="replay-actions">
              <button class="secondary-button" data-action="view" data-replay-id="${replay.id}">View</button>
              <button class="secondary-button" data-action="download" data-replay-id="${replay.id}">Download</button>
            </div>
          </div>
        `;
        replayList.appendChild(li);
      });
      if (!replayList.hasChildNodes()) {
        const li = document.createElement("li");
        li.textContent = "No arena replays yet.";
        replayList.appendChild(li);
      }
    }
  }

  private setFeedback(elementId: string, message: string, positive: boolean): void {
    const element = this.root.querySelector<HTMLParagraphElement>(`#${elementId}`);
    if (!element) return;
    element.textContent = message;
    element.dataset.status = positive ? "positive" : "negative";
  }

  private saveToken(token: string): void {
    this.token = token;
    window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
  }

  private clearToken(): void {
    this.token = null;
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
  }

  private showDashboard(): void {
    this.root.querySelector<HTMLElement>(".auth-panels")?.classList.add("hidden");
    this.root.querySelector<HTMLElement>(".arena-dashboard")?.classList.remove("hidden");
  }

  private showAuthPanels(): void {
    this.root.querySelector<HTMLElement>(".auth-panels")?.classList.remove("hidden");
    this.root.querySelector<HTMLElement>(".arena-dashboard")?.classList.add("hidden");
  }
}
