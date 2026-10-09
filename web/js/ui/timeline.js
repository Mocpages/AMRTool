import { MAX_TIMELINE_ROWS } from "../defaults.js";
import { formatLocalZulu } from "../dates.js";
import { mgrsByName } from "../fields.js";
import { rememberDraft, session } from "../session.js";
import { autoLocalTime, defaultTimeline } from "../timeline.js";

export function renderTimeline(root) {
  syncIfClean();
  root.replaceChildren(toolbar(), hint(), ...session.draft.timeline.map(rowView));
}

function syncIfClean() {
  if (session.draft.timelineDirty) return;
  session.draft.timeline = defaultTimeline(missionStub(), mgrsByName(session.zones));
}

function toolbar() {
  const bar = document.createElement("div");
  bar.className = "row";
  bar.append(action("Add event", addBlank), action("Reset from legs", reset));
  return bar;
}

function hint() {
  const note = document.createElement("p");
  note.className = "hint";
  note.textContent = "Times are local Arizona MST, written as HHMML/HHMMZ. Auto uses 200 kph, rounds up to 5 minutes, minimum 15.";
  return note;
}

function rowView(event, index) {
  const card = document.createElement("div");
  card.className = "trow";
  card.append(
    field("Date", "date", event.date, (value) => { event.date = value; touch(); }),
    field("Local HHMM", "text", event.localTime, (value) => {
      event.localTime = value;
      touch();
    }, 8, event),
    shown(event),
    field("Event", "text", event.event, (value) => { event.event = value; touch(); }, 28),
    field("Location", "text", event.location, (value) => { event.location = value.slice(0, 18); touch(); }, 18),
    actions(index),
  );
  return card;
}

function shown(event) {
  const label = document.createElement("span");
  label.className = "shown";
  label.textContent = formatLocalZulu(event.localTime) || "—";
  return label;
}

function field(labelText, type, value, onChange, width, liveEvent) {
  const wrap = document.createElement("label");
  wrap.textContent = labelText;
  const input = document.createElement("input");
  input.type = type;
  input.value = value || "";
  if (width) input.size = width;
  if (labelText === "Location") input.maxLength = 18;
  input.addEventListener("input", () => {
    onChange(input.value);
    if (!liveEvent) return;
    const shown = input.closest(".trow")?.querySelector(".shown");
    if (shown) shown.textContent = formatLocalZulu(liveEvent.localTime) || "—";
  });
  wrap.append(input);
  return wrap;
}

function actions(index) {
  const box = document.createElement("div");
  box.className = "row";
  box.append(
    action("Up", () => move(index, -1)),
    action("Down", () => move(index, 1)),
    action("Auto", () => autoRow(index)),
    action("Delete", () => remove(index)),
  );
  return box;
}

function addBlank() {
  if (session.draft.timeline.length >= MAX_TIMELINE_ROWS) return;
  session.draft.timeline.push({
    date: session.draft.missionDate,
    localTime: "",
    event: "",
    location: "",
  });
  touch();
  document.dispatchEvent(new Event("amr-refresh"));
}

function reset() {
  session.draft.timelineDirty = false;
  rememberDraft();
  document.dispatchEvent(new Event("amr-refresh"));
}

function remove(index) {
  session.draft.timeline.splice(index, 1);
  touch();
  document.dispatchEvent(new Event("amr-refresh"));
}

function move(index, delta) {
  const target = index + delta;
  const rows = session.draft.timeline;
  if (target < 0 || target >= rows.length) return;
  [rows[index], rows[target]] = [rows[target], rows[index]];
  touch();
  document.dispatchEvent(new Event("amr-refresh"));
}

function autoRow(index) {
  if (index === 0) {
    window.alert("Need a previous event to estimate time.");
    return;
  }
  const prev = session.draft.timeline[index - 1];
  const row = session.draft.timeline[index];
  try {
    row.localTime = autoLocalTime(prev.localTime, prev.location, row.location, mgrsByName(session.zones));
  } catch (err) {
    window.alert(err.message);
    return;
  }
  touch();
  document.dispatchEvent(new Event("amr-refresh"));
}

function touch() {
  session.draft.timelineDirty = true;
  rememberDraft();
}

function missionStub() {
  return { missionDate: session.draft.missionDate, legs: session.draft.legs };
}

function action(text, fn) {
  const el = document.createElement("button");
  el.type = "button";
  el.textContent = text;
  el.addEventListener("click", fn);
  return el;
}
