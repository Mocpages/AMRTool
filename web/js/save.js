import { TEMPLATE_URL } from "./defaults.js";
import { buildFieldValues, mgrsByName } from "./fields.js";
import { chipJpeg, fetchExtentImage, routeNames } from "./imagery.js";
import { overviewJpeg } from "./map.js";
import { fillPdf } from "./pdfFill.js";
import { peopleByKey } from "./roster.js";
import { session } from "./session.js";
import { loadValue, saveValue } from "./store.js";
import { todayIso } from "./dates.js";
import { validateMission } from "./validate.js";

export async function saveFilledPdf(setStatus) {
  const mission = toMission();
  const known = new Set(session.zones.map((zone) => zone.name));
  const errors = validateMission(mission, known);
  if (errors.length && !window.confirm(`${errors.map((err) => `• ${err}`).join("\n")}\n\nSave anyway?`)) {
    return;
  }
  setStatus("Downloading LZ images. The first time takes longer than later saves.");
  const chips = await loadChips(mission, setStatus);
  setStatus("Drawing route map…");
  const overview = await overviewJpeg(session.zones, mission.legs, fetchExtentImage);
  setStatus("Filling PDF…");
  const template = await fetch(TEMPLATE_URL).then((res) => res.arrayBuffer());
  const packet = buildFieldValues(mission, mgrsByName(session.zones), peopleByKey(session.roster, session.extras));
  const bytes = await fillPdf(template, { ...packet, overview, chips });
  download(bytes);
  setStatus("Saved AMR_filled.pdf in your downloads folder.");
}

async function loadChips(mission, setStatus) {
  const chips = [];
  const names = routeNames(mission);
  for (let index = 0; index < names.length; index += 1) {
    const zone = session.zones.find((item) => item.name === names[index]);
    if (!zone || !zone.mgrs) continue;
    setStatus(`LZ image ${index + 1} of ${names.length}: ${zone.name}`);
    try {
      chips.push(await cachedChip(zone));
    } catch (err) {
      console.warn(err);
    }
  }
  return chips;
}

async function cachedChip(zone) {
  const key = `chip:${zone.name}:${zone.mgrs}`;
  const hit = await loadValue(key);
  if (hit) return hit;
  const bytes = await chipJpeg(zone);
  await saveValue(key, bytes);
  return bytes;
}

function toMission() {
  const draft = session.draft;
  return {
    missionDate: draft.missionDate,
    submittedDate: todayIso(),
    unit: draft.unit,
    pocName: draft.pocName,
    pocPhone: draft.pocPhone,
    pocEmail: draft.pocEmail,
    reviewerName: draft.reviewerName,
    reviewerEmail: draft.reviewerEmail,
    statement: draft.statement,
    trainingIntent: draft.trainingIntent,
    task1: draft.task1,
    purpose1: draft.purpose1,
    description: draft.description,
    remarks: draft.remarks,
    legs: draft.legs,
    timelineDirty: draft.timelineDirty,
    timeline: draft.timeline,
  };
}

function download(bytes) {
  const blob = new Blob([bytes], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "AMR_filled.pdf";
  link.click();
  URL.revokeObjectURL(url);
}
