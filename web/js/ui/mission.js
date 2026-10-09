import { rememberCsv, rememberDraft, rememberKmz, session } from "../session.js";

export function renderMission(root) {
  const draft = session.draft;
  root.replaceChildren(
    sources(),
    dateField(draft),
    area("Mission description", draft.description, (value) => { draft.description = value; rememberDraft(); }),
    area("Remarks", draft.remarks, (value) => { draft.remarks = value; rememberDraft(); }),
    defaultsBlock(draft),
  );
}

function sources() {
  const box = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Data sources (stored only in this browser)";
  box.append(legend, sourceRow("Roster CSV", session.csvName, ".csv,text/csv", onCsv));
  box.append(sourceRow("LZ KMZ", session.kmzName, ".kmz", onKmz));
  return box;
}

function sourceRow(labelText, name, accept, onFile) {
  const row = document.createElement("div");
  row.className = "row";
  const label = document.createElement("span");
  label.textContent = `${labelText}: ${name || "(not set)"}`;
  const input = document.createElement("input");
  input.type = "file";
  input.accept = accept;
  input.addEventListener("change", () => {
    const file = input.files && input.files[0];
    if (file) onFile(file);
  });
  row.append(label, input);
  return row;
}

async function onCsv(file) {
  try {
    await rememberCsv(file);
    document.dispatchEvent(new Event("amr-refresh"));
  } catch (err) {
    window.alert(err.message);
  }
}

async function onKmz(file) {
  try {
    await rememberKmz(file);
    document.dispatchEvent(new Event("amr-refresh"));
  } catch (err) {
    window.alert(err.message);
  }
}

function dateField(draft) {
  const label = document.createElement("label");
  label.textContent = "Mission date";
  const input = document.createElement("input");
  input.type = "date";
  input.value = draft.missionDate;
  input.addEventListener("change", () => {
    draft.missionDate = input.value;
    if (!draft.timelineDirty) {
      for (const event of draft.timeline) event.date = input.value;
    }
    rememberDraft();
  });
  label.append(input);
  return label;
}

function area(title, value, onChange) {
  const label = document.createElement("label");
  label.className = "block";
  label.textContent = title;
  const text = document.createElement("textarea");
  text.rows = 4;
  text.value = value;
  text.addEventListener("input", () => onChange(text.value));
  label.append(text);
  return label;
}

function defaultsBlock(draft) {
  const box = document.createElement("fieldset");
  const legend = document.createElement("legend");
  legend.textContent = "Autofilled (editable)";
  box.append(legend);
  const rows = [
    ["Unit", "unit"],
    ["POC", "pocName"],
    ["POC phone", "pocPhone"],
    ["POC email", "pocEmail"],
    ["Reviewer / BDE BAE", "reviewerName"],
    ["Reviewer email", "reviewerEmail"],
    ["T1", "task1"],
    ["P1", "purpose1"],
  ];
  for (const [label, key] of rows) box.append(line(label, draft[key], (value) => {
    draft[key] = value;
    rememberDraft();
  }));
  box.append(area("Mission statement", draft.statement, (value) => {
    draft.statement = value;
    rememberDraft();
  }));
  box.append(area("Training intent", draft.trainingIntent, (value) => {
    draft.trainingIntent = value;
    rememberDraft();
  }));
  return box;
}

function line(title, value, onChange) {
  const label = document.createElement("label");
  label.textContent = title;
  const input = document.createElement("input");
  input.value = value;
  input.addEventListener("input", () => onChange(input.value));
  label.append(input);
  return label;
}
