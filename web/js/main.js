import { loadSession } from "./session.js";
import { saveFilledPdf } from "./save.js";
import { renderLegs } from "./ui/legs.js";
import { renderManifest } from "./ui/manifest.js";
import { renderMission } from "./ui/mission.js";
import { renderReview } from "./ui/review.js";
import { renderTimeline } from "./ui/timeline.js";

const TABS = [
  ["Mission", renderMission],
  ["Legs", renderLegs],
  ["Timeline", renderTimeline],
  ["Manifest", renderManifest],
  ["Review", renderReview],
];

let active = "Mission";

async function boot() {
  const status = document.querySelector("#status");
  try {
    await loadSession();
  } catch (err) {
    status.textContent = err.message;
  }
  drawTabs();
  show();
  document.addEventListener("amr-refresh", show);
  document.querySelector("#save").addEventListener("click", () => runSave(status));
}

function drawTabs() {
  const nav = document.querySelector("#tabs");
  nav.replaceChildren();
  for (const [name] of TABS) {
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.className = name === active ? "on" : "";
    button.addEventListener("click", () => {
      active = name;
      drawTabs();
      show();
    });
    nav.append(button);
  }
}

function show() {
  const panel = document.querySelector("#panel");
  const tab = TABS.find(([name]) => name === active);
  tab[1](panel);
}

async function runSave(status) {
  document.querySelector("#save").disabled = true;
  try {
    await saveFilledPdf((text) => { status.textContent = text; });
  } catch (err) {
    status.textContent = err.message || String(err);
  } finally {
    document.querySelector("#save").disabled = false;
  }
}

boot();
