import {
  MISSION_STATEMENT,
  PURPOSE_1,
  REQUESTING_UNIT,
  REQUESTOR_EMAIL,
  SUPPORTED_UNIT_POC,
  SUPPORTED_UNIT_POC_PHONE,
  SUPPORTED_UNIT_REVIEWER,
  TASK_1,
  TRAINING_INTENT,
  UNIT_REVIEWER_EMAIL,
} from "./defaults.js";
import { todayIso } from "./dates.js";
import { zonesFromKmz } from "./kmz.js";
import { peopleFromCsv } from "./roster.js";
import { loadValue, saveValue } from "./store.js";

export const session = {
  zones: [],
  roster: [],
  extras: [],
  draft: blankDraft(),
  csvName: "",
  kmzName: "",
};

export function blankDraft() {
  return {
    missionDate: todayIso(),
    description: "",
    remarks: "",
    unit: REQUESTING_UNIT,
    pocName: SUPPORTED_UNIT_POC,
    pocPhone: SUPPORTED_UNIT_POC_PHONE,
    pocEmail: REQUESTOR_EMAIL,
    reviewerName: SUPPORTED_UNIT_REVIEWER,
    reviewerEmail: UNIT_REVIEWER_EMAIL,
    statement: MISSION_STATEMENT,
    trainingIntent: TRAINING_INTENT,
    task1: TASK_1,
    purpose1: PURPOSE_1,
    legs: [{ start: "", end: "", pax: [] }],
    timelineDirty: false,
    timeline: [],
  };
}

export async function loadSession() {
  const csv = await loadValue("csv");
  const kmz = await loadValue("kmz");
  const draft = await loadValue("draft");
  const extras = await loadValue("extras");
  if (csv?.text) {
    session.roster = peopleFromCsv(csv.text);
    session.csvName = csv.name || "roster.csv";
  }
  if (kmz?.buffer) {
    session.zones = await zonesFromKmz(kmz.buffer);
    session.kmzName = kmz.name || "lzs.kmz";
  }
  if (draft) session.draft = { ...blankDraft(), ...draft };
  if (Array.isArray(extras)) session.extras = extras;
}

export async function rememberCsv(file) {
  const text = await file.text();
  session.roster = peopleFromCsv(text);
  session.csvName = file.name;
  await saveValue("csv", { name: file.name, text });
}

export async function rememberKmz(file) {
  const buffer = await file.arrayBuffer();
  session.zones = await zonesFromKmz(buffer);
  session.kmzName = file.name;
  await saveValue("kmz", { name: file.name, buffer });
}

export async function rememberDraft() {
  await saveValue("draft", session.draft);
  await saveValue("extras", session.extras);
}
