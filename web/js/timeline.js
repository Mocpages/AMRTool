import { hhmmDigits, isHhmm } from "./dates.js";
import { fromMgrs } from "./mgrs.js";

const CRUISE_KPH = 200;
const MIN_FLIGHT_MINUTES = 15;
const ROUND_UP_MINUTES = 5;

export function defaultTimeline(mission, lzMgrs) {
  const events = [];
  for (const leg of mission.legs) {
    events.push(legEvent(mission, "", `DEPART ${leg.start}`, leg.start, lzMgrs));
    events.push(legEvent(mission, "", `ARRIVE ${leg.end}`, leg.end, lzMgrs));
  }
  return events;
}

export function timesForLeg(leg, events, used) {
  const dep = takeTime(events, used, "DEPART", leg.start) || leg.depTime || "";
  const arr = takeTime(events, used, "ARRIVE", leg.end) || leg.arrTime || "";
  return [dep, arr];
}

export function autoLocalTime(prevHhmm, prevLocation, currLocation, lzMgrs) {
  if (!isHhmm(prevHhmm)) throw new Error("previous event needs a local HHMM time");
  const minutes = flightMinutes(distanceKm(
    latLon(prevLocation, lzMgrs),
    latLon(currLocation, lzMgrs),
  ));
  return addHhmm(prevHhmm, minutes);
}

export function flightMinutes(km) {
  if (km <= 0) return MIN_FLIGHT_MINUTES;
  const raw = km / CRUISE_KPH * 60;
  const rounded = Math.ceil(raw / ROUND_UP_MINUTES) * ROUND_UP_MINUTES;
  return Math.max(MIN_FLIGHT_MINUTES, rounded);
}

function takeTime(events, used, verb, lzName) {
  if (!lzName) return "";
  const verbU = verb.toUpperCase();
  const lzU = lzName.toUpperCase();
  for (let index = 0; index < events.length; index += 1) {
    if (used.has(index)) continue;
    const text = (events[index].event || "").toUpperCase();
    if (text.includes(verbU) && text.includes(lzU)) {
      used.add(index);
      return events[index].localTime || "";
    }
  }
  return "";
}

function distanceKm(a, b) {
  const lat1 = a[0] * Math.PI / 180;
  const lon1 = a[1] * Math.PI / 180;
  const lat2 = b[0] * Math.PI / 180;
  const lon2 = b[1] * Math.PI / 180;
  const dLat = lat2 - lat1;
  const dLon = lon2 - lon1;
  const chord = Math.sin(dLat / 2) ** 2
    + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.min(1, Math.sqrt(chord)));
}

function addHhmm(hhmm, minutes) {
  const digits = hhmmDigits(hhmm);
  const total = (Number(digits.slice(0, 2)) * 60 + Number(digits.slice(2)) + minutes) % (24 * 60);
  const fixed = (total + 24 * 60) % (24 * 60);
  return `${String(Math.floor(fixed / 60)).padStart(2, "0")}${String(fixed % 60).padStart(2, "0")}`;
}

function latLon(location, lzMgrs) {
  const text = (location || "").trim();
  if (!text) throw new Error("location is empty");
  const mgrs = lzMgrs[text] || text;
  if (!mgrs) throw new Error(`no grid for ${text}`);
  return fromMgrs(mgrs);
}

function legEvent(mission, localTime, event, lzName, lzMgrs) {
  return {
    date: mission.missionDate,
    localTime,
    event,
    location: lzMgrs[lzName] || lzName,
  };
}
