import { formatIsoDate, formatLocalZulu } from "../dates.js";
import { maxPax, mgrsByName } from "../fields.js";
import { rowCount } from "../manifest.js";
import { session } from "../session.js";
import { defaultTimeline, timesForLeg } from "../timeline.js";
import { MAX_MANIFEST_ROWS } from "../defaults.js";

export function renderReview(root) {
  const pre = document.createElement("pre");
  pre.textContent = summary().join("\n");
  root.replaceChildren(pre);
}

function summary() {
  const draft = session.draft;
  const rows = rowCount(draftToMission());
  const pages = rows ? Math.ceil(rows / MAX_MANIFEST_ROWS) : 0;
  const lines = [
    `Mission date: ${draft.missionDate}`,
    `Unit: ${draft.unit}`,
    `Passenger count (largest leg): ${maxPax(draftToMission())}`,
    `Manifest rows: ${rows} (${pages} page${pages === 1 ? "" : "s"})`,
    "",
    "Legs:",
  ];
  const events = timelineEvents();
  const used = new Set();
  draft.legs.forEach((leg, index) => {
    const [dep, arr] = timesForLeg(leg, events, used);
    lines.push(`  ${index + 1}. ${leg.start || "?"} → ${leg.end || "?"}  ${formatLocalZulu(dep) || "----"} / ${formatLocalZulu(arr) || "----"}  pax ${leg.pax.length}`);
  });
  lines.push("", "Timeline:");
  for (const event of events) {
    lines.push(`  ${formatIsoDate(event.date)} ${formatLocalZulu(event.localTime) || "----"}  ${event.event}  ${event.location}`);
  }
  lines.push("", "LZs:");
  const grids = mgrsByName(session.zones);
  for (const name of new Set(draft.legs.flatMap((leg) => [leg.start, leg.end]).filter(Boolean))) {
    lines.push(`  ${name}: ${grids[name] || "unknown"}`);
  }
  return lines;
}

function timelineEvents() {
  if (session.draft.timelineDirty) return session.draft.timeline;
  return defaultTimeline(draftToMission(), mgrsByName(session.zones));
}

function draftToMission() {
  return {
    missionDate: session.draft.missionDate,
    legs: session.draft.legs,
    timelineDirty: session.draft.timelineDirty,
    timeline: session.draft.timeline,
  };
}
