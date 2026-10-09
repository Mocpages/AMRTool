import { LOCAL_UTC_OFFSET_HOURS } from "./defaults.js";

export const MONTHS = [
  "JAN", "FEB", "MAR", "APR", "MAY", "JUN",
  "JUL", "AUG", "SEP", "OCT", "NOV", "DEC",
];

export function formatDate(value) {
  const day = String(value.getUTCDate()).padStart(2, "0");
  const month = MONTHS[value.getUTCMonth()];
  const year = String(value.getUTCFullYear()).slice(-2);
  return `${day} ${month} ${year}`;
}

export function formatIsoDate(iso) {
  if (!iso || !String(iso).includes("-")) return "";
  const [year, month, day] = iso.split("-").map(Number);
  return formatDate(new Date(Date.UTC(year, month - 1, day)));
}

export function hhmmDigits(text) {
  return [...String(text || "")].filter((ch) => ch >= "0" && ch <= "9").join("").slice(0, 4);
}

export function isHhmm(text) {
  const digits = hhmmDigits(text);
  if (digits.length !== 4) return false;
  const hour = Number(digits.slice(0, 2));
  const minute = Number(digits.slice(2));
  return hour >= 0 && hour <= 23 && minute >= 0 && minute <= 59;
}

export function localToZulu(hhmm) {
  const digits = hhmmDigits(hhmm);
  const minutes = Number(digits.slice(0, 2)) * 60 + Number(digits.slice(2));
  const zulu = (minutes - LOCAL_UTC_OFFSET_HOURS * 60) % (24 * 60);
  const fixed = (zulu + 24 * 60) % (24 * 60);
  return `${String(Math.floor(fixed / 60)).padStart(2, "0")}${String(fixed % 60).padStart(2, "0")}`;
}

export function formatLocalZulu(hhmm) {
  if (!isHhmm(hhmm)) return "";
  const local = hhmmDigits(hhmm);
  return `${local}L/${localToZulu(local)}Z`;
}

export function todayIso() {
  const now = new Date();
  const y = now.getFullYear();
  const m = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
