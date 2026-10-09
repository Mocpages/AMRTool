import { isHhmm } from "./dates.js";
import { MAX_HLZ_ROWS, MAX_LEGS, MAX_TIMELINE_ROWS } from "./defaults.js";
import { uniqueLzNames } from "./fields.js";

export function validateMission(mission, knownLzs) {
  return [
    ...textErrors(mission),
    ...legErrors(mission, knownLzs),
    ...timelineErrors(mission),
    ...lzCountErrors(mission),
  ];
}

function textErrors(mission) {
  const errors = [];
  if (!mission.description.trim()) errors.push("mission description is required");
  if (!mission.remarks.trim()) errors.push("remarks are required");
  if (!mission.legs.length) errors.push("add at least one leg");
  if (mission.legs.length > MAX_LEGS) errors.push(`at most ${MAX_LEGS} legs`);
  return errors;
}

function legErrors(mission, knownLzs) {
  const errors = [];
  mission.legs.forEach((leg, index) => {
    const prefix = `leg ${index + 1}`;
    if (!leg.start || !leg.end) errors.push(`${prefix}: select start and end LZs`);
    else if (leg.start === leg.end) errors.push(`${prefix}: start and end LZ must differ`);
    for (const name of [leg.start, leg.end]) {
      if (name && !knownLzs.has(name)) errors.push(`${prefix}: unknown LZ ${name}`);
    }
  });
  return errors;
}

function timelineErrors(mission) {
  if (!mission.timelineDirty) return [];
  const events = mission.timeline.filter((event) => event.event || event.localTime);
  const errors = [];
  if (events.length > MAX_TIMELINE_ROWS) {
    errors.push(`timeline has ${events.length} events; PDF allows ${MAX_TIMELINE_ROWS}`);
  }
  events.forEach((event, index) => {
    if (!isHhmm(event.localTime)) errors.push(`timeline ${index + 1}: time must be local HHMM`);
    if (!event.event) errors.push(`timeline ${index + 1}: event text is required`);
  });
  return errors;
}

function lzCountErrors(mission) {
  const count = uniqueLzNames(mission).length;
  if (count > MAX_HLZ_ROWS) {
    return [`${count} unique LZs; CONOP table allows ${MAX_HLZ_ROWS}`];
  }
  return [];
}
