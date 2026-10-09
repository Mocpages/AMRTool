import { personKey, squadsInOrder } from "../roster.js";
import { rememberDraft, session } from "../session.js";

let currentLeg = 0;

export function renderManifest(root) {
  if (currentLeg >= session.draft.legs.length) currentLeg = 0;
  root.replaceChildren(toolbar(), groups());
}

function toolbar() {
  const bar = document.createElement("div");
  bar.className = "row";
  const select = document.createElement("select");
  session.draft.legs.forEach((_, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `Leg ${index + 1}`;
    if (index === currentLeg) option.selected = true;
    select.append(option);
  });
  select.addEventListener("change", () => {
    currentLeg = Number(select.value);
    document.dispatchEvent(new Event("amr-refresh"));
  });
  bar.append(labelWrap("Leg", select), addForm());
  return bar;
}

function groups() {
  const box = document.createElement("div");
  const people = [...session.roster, ...session.extras];
  const selected = new Set(session.draft.legs[currentLeg]?.pax || []);
  for (const squad of ["", ...squadsInOrder(people)]) {
    const members = people.filter((person) => (squad ? person.squad === squad : !person.squad));
    if (!members.length) continue;
    box.append(squadBlock(squad || "Unassigned", members, selected));
  }
  return box;
}

function squadBlock(title, members, selected) {
  const card = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = title;
  card.append(legend, squadActions(title, members));
  for (const person of members) card.append(personRow(person, selected));
  return card;
}

function squadActions(title, members) {
  const row = document.createElement("div");
  row.className = "row";
  row.append(action(`Select ${title}`, () => setGroup(members, true)));
  row.append(action("Clear", () => setGroup(members, false)));
  return row;
}

function setGroup(members, on) {
  const leg = session.draft.legs[currentLeg];
  const keys = new Set(leg.pax);
  for (const person of members) {
    const key = personKey(person);
    if (on) keys.add(key);
    else keys.delete(key);
  }
  const order = [...session.roster, ...session.extras].map(personKey);
  leg.pax = order.filter((item) => keys.has(item));
  rememberDraft();
  document.dispatchEvent(new Event("amr-refresh"));
}

function action(text, fn) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = text;
  button.addEventListener("click", fn);
  return button;
}

function personRow(person, selected) {
  const key = personKey(person);
  const label = document.createElement("label");
  label.className = "check";
  const input = document.createElement("input");
  input.type = "checkbox";
  input.checked = selected.has(key);
  input.addEventListener("change", () => toggle(key, input.checked));
  label.append(input, document.createTextNode(`${person.rank} ${person.lastName} ${person.lastFour}`));
  return label;
}

function toggle(key, on) {
  const leg = session.draft.legs[currentLeg];
  const keys = new Set(leg.pax);
  if (on) keys.add(key);
  else keys.delete(key);
  const order = [...session.roster, ...session.extras].map(personKey);
  leg.pax = order.filter((item) => keys.has(item));
  rememberDraft();
}

function addForm() {
  const form = document.createElement("form");
  form.className = "row";
  const rank = textInput("Rank", 8);
  const last = textInput("Last", 16);
  const four = textInput("Last 4", 6);
  const submit = document.createElement("button");
  submit.type = "submit";
  submit.textContent = "Add person";
  form.append(rank.label, last.label, four.label, submit);
  form.addEventListener("submit", (event) => {
    event.preventDefault();
    addPerson(rank.input.value, last.input.value, four.input.value);
  });
  return form;
}

function addPerson(rank, last, four) {
  const person = {
    rank: rank.trim(),
    lastName: last.trim(),
    lastFour: four.trim().padStart(4, "0"),
    squad: "",
  };
  if (!person.rank || !person.lastName || !four.trim()) return;
  session.extras.push(person);
  rememberDraft();
  document.dispatchEvent(new Event("amr-refresh"));
}

function textInput(name, size) {
  const label = document.createElement("label");
  label.textContent = name;
  const input = document.createElement("input");
  input.size = size;
  label.append(input);
  return { label, input };
}

function labelWrap(text, control) {
  const label = document.createElement("label");
  label.textContent = text;
  label.append(control);
  return label;
}
