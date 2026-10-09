import { SQUAD_ORDER } from "./defaults.js";

export function personKey(person) {
  return `${person.rank}|${person.lastName}|${person.lastFour}`;
}

export function peopleFromCsv(text) {
  return parseCsv(text).map(rowToPerson).filter(Boolean);
}

export function peopleByKey(roster, extras) {
  const index = {};
  for (const person of roster) index[personKey(person)] = person;
  for (const person of extras) index[personKey(person)] = person;
  return index;
}

export function squadsInOrder(people) {
  const present = new Set(people.map((person) => person.squad).filter(Boolean));
  const ordered = SQUAD_ORDER.filter((name) => present.has(name));
  const extras = [...present].filter((name) => !SQUAD_ORDER.includes(name)).sort();
  return [...ordered, ...extras];
}

function rowToPerson(row) {
  const rank = (row.Rank || "").trim();
  const lastName = (row.Last || "").trim();
  const raw = (row["DODID (L4)"] || "").trim();
  const lastFour = raw.padStart(4, "0");
  const squad = (row.Squad || "").trim();
  if (!rank || !lastName || !raw) return null;
  return { rank, lastName, lastFour, squad };
}

function parseCsv(text) {
  const rows = splitRecords(stripBom(text));
  if (!rows.length) return [];
  const headers = splitLine(rows[0]);
  return rows.slice(1).filter((line) => line.trim()).map((line) => {
    const cells = splitLine(line);
    const row = {};
    headers.forEach((header, index) => {
      row[header.trim()] = cells[index] || "";
    });
    return row;
  });
}

function stripBom(text) {
  return text.charCodeAt(0) === 0xfeff ? text.slice(1) : text;
}

function splitRecords(text) {
  return text.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
}

function splitLine(line) {
  const cells = [];
  let current = "";
  let quoted = false;
  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (quoted && ch === '"' && line[i + 1] === '"') {
      current += '"';
      i += 1;
    } else if (ch === '"') {
      quoted = !quoted;
    } else if (ch === "," && !quoted) {
      cells.push(current);
      current = "";
    } else {
      current += ch;
    }
  }
  cells.push(current);
  return cells;
}
