import { MAX_MANIFEST_ROWS, NATIONALITY, NO_TROOPS_LABEL, SERVICE } from "./defaults.js";

export function pageValues(mission, people) {
  const lines = buildLines(mission, people);
  if (!lines.length) return [{}];
  const pages = [];
  for (let start = 0; start < lines.length; start += MAX_MANIFEST_ROWS) {
    pages.push(fieldsForPage(lines.slice(start, start + MAX_MANIFEST_ROWS)));
  }
  return pages;
}

export function rowCount(mission) {
  return mission.legs.reduce((sum, leg) => sum + (leg.pax.length || 1), 0);
}

export function buildLines(mission, people) {
  const lines = [];
  mission.legs.forEach((leg, index) => {
    const number = index + 1;
    if (!leg.pax.length) lines.push(noTroopsLine(number, leg));
    else lines.push(...paxLines(number, leg, people));
  });
  return lines;
}

function noTroopsLine(legNumber, leg) {
  return {
    lastName: NO_TROOPS_LABEL,
    rank: "",
    lastFour: "",
    pickup: leg.start,
    dropoff: leg.end,
    legNumber,
    noTroops: true,
  };
}

function paxLines(number, leg, people) {
  return leg.pax.map((key) => people[key]).filter(Boolean).map((person) => ({
    lastName: person.lastName,
    rank: person.rank,
    lastFour: person.lastFour,
    pickup: leg.start,
    dropoff: leg.end,
    legNumber: number,
    noTroops: false,
  }));
}

function fieldsForPage(lines) {
  const values = {};
  lines.forEach((line, index) => Object.assign(values, lineFields(line, index + 1)));
  return values;
}

function lineFields(line, row) {
  const mark = { [`${line.legNumber}Row${row}`]: "X" };
  const places = {
    [`Last NameRow${row}`]: line.lastName,
    [`PickUp LocationRow${row}`]: line.pickup,
    [`DropOff LocationRow${row}`]: line.dropoff,
  };
  if (line.noTroops) return { ...places, ...mark };
  return {
    [`RankRow${row}`]: line.rank,
    ...places,
    [`NationalityRow${row}`]: NATIONALITY,
    [`ServiceRow${row}`]: SERVICE,
    [`Last 4 IDSSNRow${row}`]: line.lastFour,
    ...mark,
  };
}
