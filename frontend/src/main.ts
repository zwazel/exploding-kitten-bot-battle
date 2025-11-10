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
      <h1>Exploding Kitten Arena</h1>
      <p class="tagline">Upload bots, battle the arena, and watch replays.</p>
    </header>
    <nav class="app-nav">
      <button class="nav-btn active" data-view="viewer">Replay Viewer</button>
      <button class="nav-btn" data-view="arena">Arena</button>
    </nav>
    <main class="app-main">
      <section id="viewer-section" data-section="viewer">
        <div id="viewer-root"></div>
      </section>
      <section id="arena-section" data-section="arena" class="hidden">
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

function activateView(view: "viewer" | "arena"): void {
  sections.forEach((section) => {
    section.classList.toggle("hidden", section.dataset.section !== view);
  });
  navButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
}

navButtons.forEach((button) => {
  button.addEventListener("click", () => {
    const view = (button.dataset.view as "viewer" | "arena") || "viewer";
    activateView(view);
  });
});

new ArenaApp(arenaRoot, replayApp, {
  onShowReplay: () => activateView("viewer"),
});
