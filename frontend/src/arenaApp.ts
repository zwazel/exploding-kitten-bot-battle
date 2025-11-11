import {
  createBot,
  deleteBot,
  downloadReplayFile,
  fetchReplayMetadata,
  getApiBaseUrl,
  getBotProfile,
  getCurrentUser,
  listBots,
  login,
  signup,
  uploadBotFile,
} from "./api/client";
import type { BotProfile, BotSummary, ReplaySummary, User } from "./api/types";
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
  private bots: BotSummary[] = [];
  private selectedBotId: number | null = null;
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
    this.attachBotManagementHandlers();
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

          <section class="card bot-management">
            <h3>Manage bots</h3>
            <form id="create-bot-form" class="bot-create-form">
              <label for="bot-name">New bot name</label>
              <input id="bot-name" name="bot_name" type="text" pattern="[A-Za-z0-9_\\-]+" minlength="1" maxlength="120" required />
              <button type="submit" class="primary-button">Create bot</button>
            </form>
            <div class="bot-selector">
              <label for="bot-select">Your bots</label>
              <select id="bot-select"></select>
              <button type="button" id="refresh-bots" class="secondary-button">Refresh</button>
              <button type="button" id="delete-bot" class="secondary-button">Delete selected</button>
            </div>
            <p class="form-feedback" id="bot-feedback"></p>
          </section>

          <section class="card upload-card">
            <h3>Upload a new version</h3>
            <p class="subtle">Selected bot: <span id="selected-bot-name">None</span></p>
            <form id="upload-form" class="upload-form">
              <input type="file" id="bot-file" name="bot" accept=".py" required />
              <button type="submit" class="primary-button">Upload &amp; run arena match</button>
            </form>
            <p class="subtle">Uploading a new file adds a version for the selected bot. The arena will immediately run a match and record the replay.</p>
            <p class="form-feedback" id="upload-feedback"></p>
          </section>

          <section class="card" id="current-bot-card">
            <h3>Bot details</h3>
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
      void this.bootstrapProfile();
    } else {
      this.showAuthPanels();
    }
  }

  private async bootstrapProfile(): Promise<void> {
    if (!this.token) return;
    try {
      this.user = await getCurrentUser(this.token);
      await this.reloadBots();
      this.showDashboard();
      this.updateDashboard();
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
      this.bots = [];
      this.selectedBotId = null;
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
      if (!this.selectedBotId) {
        this.setFeedback("upload-feedback", "Create and select a bot first.", false);
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
        const result = await uploadBotFile(this.token, this.selectedBotId, file);
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
        await this.reloadBots(this.selectedBotId);
      } catch (error) {
        this.setFeedback("upload-feedback", (error as Error).message, false);
      } finally {
        uploadForm.reset();
      }
    });
  }

  private attachBotManagementHandlers(): void {
    const createForm = this.root.querySelector<HTMLFormElement>("#create-bot-form");
    const select = this.root.querySelector<HTMLSelectElement>("#bot-select");
    const refreshButton = this.root.querySelector<HTMLButtonElement>("#refresh-bots");
    const deleteButton = this.root.querySelector<HTMLButtonElement>("#delete-bot");

    createForm?.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!this.token) {
        this.setFeedback("bot-feedback", "Log in to create bots.", false);
        return;
      }
      const formData = new FormData(createForm);
      const name = (formData.get("bot_name") as string).trim();
      if (!name) {
        this.setFeedback("bot-feedback", "Provide a bot name.", false);
        return;
      }
      try {
        this.setFeedback("bot-feedback", "Creating bot…", true);
        const summary = await createBot(this.token, name);
        await this.reloadBots(summary.id);
        this.setFeedback("bot-feedback", `Bot ${summary.qualified_name} created.`, true);
        createForm.reset();
      } catch (error) {
        this.setFeedback("bot-feedback", (error as Error).message, false);
      }
    });

    select?.addEventListener("change", async () => {
      const value = select.value;
      this.selectedBotId = value ? Number.parseInt(value, 10) : null;
      await this.loadSelectedBot();
      this.updateDashboard();
    });

    refreshButton?.addEventListener("click", async () => {
      await this.reloadBots(this.selectedBotId);
      this.setFeedback("bot-feedback", "Bots refreshed.", true);
    });

    deleteButton?.addEventListener("click", async () => {
      if (!this.token || !this.selectedBotId) {
        this.setFeedback("bot-feedback", "Select a bot to delete.", false);
        return;
      }
      try {
        await deleteBot(this.token, this.selectedBotId);
        await this.reloadBots();
        this.setFeedback("bot-feedback", "Bot deleted.", true);
      } catch (error) {
        this.setFeedback("bot-feedback", (error as Error).message, false);
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

  private async reloadBots(preferredId?: number | null): Promise<void> {
    if (!this.token) return;
    this.bots = await listBots(this.token);
    const selectElement = this.root.querySelector<HTMLSelectElement>("#bot-select");
    const previousSelection = this.selectedBotId;
    this.selectedBotId = null;
    if (this.bots.length > 0) {
      const desired = preferredId ?? previousSelection ?? this.bots[0].id;
      const found = this.bots.find((bot) => bot.id === desired) ?? this.bots[0];
      this.selectedBotId = found.id;
    }
    this.renderBotSelector();
    await this.loadSelectedBot();
    this.updateDashboard();
    if (selectElement) {
      selectElement.value = this.selectedBotId !== null ? String(this.selectedBotId) : "";
    }
  }

  private async loadSelectedBot(): Promise<void> {
    if (!this.token || this.selectedBotId === null) {
      this.profile = null;
      return;
    }
    try {
      this.profile = await getBotProfile(this.token, this.selectedBotId);
    } catch (error) {
      console.error("Unable to fetch bot profile", error);
      this.profile = null;
    }
  }

  private renderBotSelector(): void {
    const select = this.root.querySelector<HTMLSelectElement>("#bot-select");
    const selectedName = this.root.querySelector<HTMLSpanElement>("#selected-bot-name");
    if (!select || !selectedName) return;

    select.innerHTML = "";
    if (this.bots.length === 0) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "No bots yet";
      select.appendChild(option);
      select.disabled = true;
      selectedName.textContent = "None";
    } else {
      this.bots.forEach((bot) => {
        const option = document.createElement("option");
        option.value = String(bot.id);
        option.textContent = bot.qualified_name;
        if (bot.id === this.selectedBotId) {
          option.selected = true;
        }
        select.appendChild(option);
      });
      select.disabled = false;
      const active = this.bots.find((bot) => bot.id === this.selectedBotId);
      selectedName.textContent = active ? active.qualified_name : "None";
    }

    const uploadForm = this.root.querySelector<HTMLFormElement>("#upload-form");
    const uploadInputs = uploadForm ? Array.from(uploadForm.elements) : [];
    uploadInputs.forEach((element) => {
      if (element instanceof HTMLInputElement || element instanceof HTMLButtonElement) {
        element.disabled = this.selectedBotId === null;
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
      info.textContent = `${this.user.display_name} (@${this.user.username}) · ${this.user.email}`;
    }
    if (apiInfo) {
      apiInfo.textContent = `API base: ${getApiBaseUrl()}`;
    }

    if (currentBotContainer) {
      if (!this.profile) {
        currentBotContainer.innerHTML = `<p>No bot selected. Create or choose a bot to view details.</p>`;
      } else {
        const currentVersion = this.profile.current_version;
        const createdText = formatDate(this.profile.created_at);
        const versionInfo = currentVersion
          ? `Active version <strong>${currentVersion.version_number}</strong> uploaded ${formatDate(currentVersion.created_at)}.`
          : "No versions uploaded yet.";
        currentBotContainer.innerHTML = `
          <p><strong>${this.profile.qualified_name}</strong></p>
          <p>Created ${createdText}. ${versionInfo}</p>
        `;
      }
    }

    if (versionsList) {
      versionsList.innerHTML = "";
      if (!this.profile || this.profile.versions.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No versions yet.";
        versionsList.appendChild(li);
      } else {
        this.profile.versions.forEach((version) => {
          const li = document.createElement("li");
          li.textContent = `${version.version_number}. uploaded ${formatDate(version.created_at)}${version.is_active ? " (active)" : ""}`;
          versionsList.appendChild(li);
        });
      }
    }

    if (replayList) {
      replayList.innerHTML = "";
      if (!this.profile || this.profile.recent_replays.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No arena replays yet.";
        replayList.appendChild(li);
      } else {
        this.profile.recent_replays.forEach((replay) => {
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
      }
    }
  }

  private setFeedback(elementId: string, message: string, positive: boolean): void {
    const element = this.root.querySelector<HTMLParagraphElement>(`#${elementId}`);
    if (!element) return;
    element.textContent = message;
    if (!message) {
      delete element.dataset.status;
    } else {
      element.dataset.status = positive ? "positive" : "negative";
    }
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
