import "./style.css";
import { ArenaApp } from "./arenaApp";
import { ReplayApp } from "./replayApp";

const root = document.querySelector<HTMLDivElement>("#app");
if (!root) {
  throw new Error("App root element #app not found");
}

root.innerHTML = `
  <div class="app-shell">
    <header class="app-header">
      <h1 class="app-title">Exploding Kittens Command Center</h1>
      <p class="tagline">Watch replays, run bot battles, and keep your roster sharp.</p>
    </header>
    <nav class="app-nav" role="tablist" aria-label="Primary">
      <button class="nav-btn active" data-view="viewer" role="tab" aria-selected="true">Replay Viewer</button>
      <button class="nav-btn" data-view="bots" role="tab" aria-selected="false">Bots</button>
    </nav>
    <main class="app-main">
      <section id="viewer-section" data-section="viewer">
        <div id="viewer-root"></div>
      </section>
      <section id="arena-section" data-section="bots" class="hidden">
        <div id="arena-root"></div>
      </section>
    </main>
  </div>
`;

const viewerRoot = root.querySelector<HTMLDivElement>("#viewer-root");
const arenaRoot = root.querySelector<HTMLDivElement>("#arena-root");
if (!viewerRoot || !arenaRoot) {
  throw new Error("Failed to initialize UI containers");
}

const replayApp = new ReplayApp(viewerRoot);

const navButtons = Array.from(root.querySelectorAll<HTMLButtonElement>(".nav-btn"));
const sections = Array.from(root.querySelectorAll<HTMLElement>("[data-section]"));

function activateView(view: "viewer" | "bots"): void {
  sections.forEach((section) => {
    section.classList.toggle("hidden", section.dataset.section !== view);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
    button.setAttribute("aria-selected", button.dataset.view === view ? "true" : "false");
  });
  replayApp.handleVisibilityChange(view === "viewer");
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const view = (button.dataset.view as "viewer" | "bots") || "viewer";
    activateView(view);
  });
});

new ArenaApp(arenaRoot, replayApp, {
  onShowReplay: () => activateView("viewer"),
});
