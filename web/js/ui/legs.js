import { MAX_LEGS } from "../defaults.js";
import { rememberDraft, session } from "../session.js";

export function renderLegs(root) {
  root.replaceChildren(toolbar(), hint(), ...session.draft.legs.map(legCard));
}

function toolbar() {
  const bar = document.createElement("div");
  bar.className = "row";
  bar.append(button("Add leg", addLeg), button("Remove last", removeLast));
  return bar;
}

function hint() {
  const note = document.createElement("p");
  note.className = "hint";
  note.textContent = "Set departure and arrival times on the Timeline tab.";
  return note;
}

function legCard(leg, index) {
  const card = document.createElement("fieldset");
  const title = document.createElement("legend");
  title.textContent = `Leg ${index + 1}`;
  const start = lzInput("Start LZ", leg.start, (value) => { leg.start = value; rememberDraft(); });
  const end = lzInput("End LZ", leg.end, (value) => { leg.end = value; rememberDraft(); });
  card.append(title, start, end);
  return card;
}

function lzInput(labelText, value, onChange) {
  const wrap = document.createElement("label");
  wrap.className = "lz-pick";
  wrap.textContent = labelText;
  const input = document.createElement("input");
  input.value = value;
  input.autocomplete = "off";
  const list = document.createElement("ul");
  list.className = "lz-matches";
  list.hidden = true;
  input.addEventListener("input", () => {
    onChange(input.value.trim());
    showMatches(list, input, onChange);
  });
  input.addEventListener("keydown", (event) => moveMatch(event, list, input, onChange));
  input.addEventListener("focus", () => showMatches(list, input, onChange));
  input.addEventListener("blur", () => setTimeout(() => { list.hidden = true; }, 150));
  wrap.append(input, list);
  return wrap;
}

function showMatches(list, input, onChange) {
  const names = matchingNames(session.zones.map((zone) => zone.name), input.value);
  list.replaceChildren();
  for (const name of names.slice(0, 8)) {
    const item = document.createElement("li");
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = name;
    button.addEventListener("mousedown", (event) => {
      event.preventDefault();
      chooseName(list, input, onChange, name);
    });
    item.append(button);
    list.append(item);
  }
  list.hidden = names.length === 0;
}

function moveMatch(event, list, input, onChange) {
  const buttons = [...list.querySelectorAll("button")];
  if (!buttons.length || (event.key !== "ArrowDown" && event.key !== "ArrowUp" && event.key !== "Enter")) {
    return;
  }
  event.preventDefault();
  const current = buttons.findIndex((button) => button.classList.contains("active"));
  if (event.key === "Enter" && current >= 0) {
    chooseName(list, input, onChange, buttons[current].textContent);
    return;
  }
  const next = event.key === "ArrowUp" ? Math.max(0, current - 1) : Math.min(buttons.length - 1, current + 1);
  buttons.forEach((button) => button.classList.remove("active"));
  buttons[next].classList.add("active");
}

function chooseName(list, input, onChange, name) {
  input.value = name;
  onChange(name);
  list.hidden = true;
}

function matchingNames(options, query) {
  const needle = query.trim().toLowerCase().replace(/\s+/g, " ");
  if (!needle) return options;
  return options.filter((name) => name.toLowerCase().includes(needle)).sort((a, b) => rank(a, needle) - rank(b, needle) || a.localeCompare(b));
}

function rank(name, needle) {
  const lower = name.toLowerCase();
  const bare = lower.startsWith("lz ") ? lower.slice(3) : lower;
  return lower.startsWith(needle) || bare.startsWith(needle) ? 0 : 1;
}

function addLeg() {
  if (session.draft.legs.length >= MAX_LEGS) return;
  const previous = session.draft.legs.at(-1);
  session.draft.legs.push({ start: previous?.end || "", end: "", pax: [] });
  session.draft.timelineDirty = false;
  rememberDraft();
  document.dispatchEvent(new Event("amr-refresh"));
}

function removeLast() {
  if (session.draft.legs.length <= 1) return;
  session.draft.legs.pop();
  session.draft.timelineDirty = false;
  rememberDraft();
  document.dispatchEvent(new Event("amr-refresh"));
}

function button(text, action) {
  const el = document.createElement("button");
  el.type = "button";
  el.textContent = text;
  el.addEventListener("click", action);
  return el;
}
