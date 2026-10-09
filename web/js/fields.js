import {
  AIRCRAFT_ASSIGNED,
  MAX_HLZ_ROWS,
  MAX_TIMELINE_ROWS,
  MISSION_PRIORITY,
  WEIGHT_PER_PERSON,
} from "./defaults.js";
import { formatIsoDate, formatLocalZulu } from "./dates.js";
import { pageValues } from "./manifest.js";
import { defaultTimeline, timesForLeg } from "./timeline.js";

export function buildFieldValues(mission, lzMgrs, people) {
  const values = {
    ...adminFields(mission),
    ...planningFields(mission),
    ...hlzTableFields(mission),
    ...section3Fields(),
    ...conopFields(mission, lzMgrs),
  };
  const pages = pageValues(mission, people);
  return { values, extraManifest: pages.slice(1), firstPage: pages[0] || {} };
}

function adminFields(mission) {
  const missionDate = formatIsoDate(mission.missionDate);
  return {
    "MSN Dates": missionDate,
    "Mission Date": missionDate,
    "DTG Request Submitted": formatIsoDate(mission.submittedDate),
    "Supported Unit": mission.unit,
    "Supported Unit POC": mission.pocName,
    "Supported Unit POC Phone": mission.pocPhone,
    "Supported Unit POC Email": mission.pocEmail,
    "Supported Unit Reviewer": mission.reviewerName,
    "Unit Reviewer Email": mission.reviewerEmail,
    "Mission Priority Number:": MISSION_PRIORITY,
  };
}

function planningFields(mission) {
  return {
    "Supported Unit Mission StatementRow1": mission.statement,
    "Supported Unit Training Intent  End StateRow1": mission.trainingIntent,
    T1: mission.task1,
    P1: mission.purpose1,
    "Passenger Count": String(maxPax(mission)),
    "Weight  Person": WEIGHT_PER_PERSON,
    UH_2: AIRCRAFT_ASSIGNED,
    "Special-Instructions1": mission.description,
    Remarks: mission.remarks,
  };
}

function hlzTableFields(mission) {
  const values = {};
  const events = activeTimeline(mission, {});
  const used = new Set();
  mission.legs.forEach((leg, index) => {
    const number = index + 1;
    const [dep, arr] = timesForLeg(leg, events, used);
    values[`Dep Time${number}`] = formatLocalZulu(dep);
    values[`FROM${number}`] = leg.start;
    values[`TO${number}`] = leg.end;
    values[`Arr Time${number}`] = formatLocalZulu(arr);
    values[`${number}Total Pax Count Per Leg`] = String(leg.pax.length);
  });
  return values;
}

function section3Fields() {
  const values = { Group1: "No" };
  for (let index = 1; index <= 6; index += 1) {
    values[index === 1 ? "Yes" : `Yes${index}`] = false;
    values[index === 1 ? "No" : `No${index}`] = true;
  }
  for (let index = 1; index <= 5; index += 1) values[`waiver${index}`] = "No";
  for (let index = 1; index <= 8; index += 1) values[`Special${index}`] = "No";
  return values;
}

function conopFields(mission, lzMgrs) {
  const values = timelineFields(mission, lzMgrs);
  uniqueLzNames(mission).slice(0, MAX_HLZ_ROWS).forEach((name, index) => {
    values[`HLZ NameRow${index + 1}`] = name;
    values[`GridsRow${index + 1}`] = lzMgrs[name] || "";
  });
  return values;
}

function timelineFields(mission, lzMgrs) {
  const values = {};
  const events = activeTimeline(mission, lzMgrs).filter((event) => event.event || event.localTime);
  events.slice(0, MAX_TIMELINE_ROWS).forEach((event, index) => {
    const row = index + 1;
    values[`Date ${row}`] = formatIsoDate(event.date);
    values[`Time(MPT)${row}`] = formatLocalZulu(event.localTime);
    values[`EventRow${row}`] = event.event;
    values[`LocationRow${row}`] = event.location;
  });
  return values;
}

function activeTimeline(mission, lzMgrs) {
  if (mission.timelineDirty) return mission.timeline;
  return defaultTimeline(mission, lzMgrs);
}

export function uniqueLzNames(mission) {
  const seen = [];
  for (const leg of mission.legs) {
    for (const name of [leg.start, leg.end]) {
      if (name && !seen.includes(name)) seen.push(name);
    }
  }
  return seen;
}

export function maxPax(mission) {
  if (!mission.legs.length) return 0;
  return Math.max(...mission.legs.map((leg) => leg.pax.length));
}

export function mgrsByName(zones) {
  const map = {};
  for (const zone of zones) map[zone.name] = zone.mgrs;
  return map;
}
