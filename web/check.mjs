import { readFileSync } from "node:fs";
import { PDFDocument } from "./vendor/pdf-lib.esm.min.js";
import { buildFieldValues } from "./js/fields.js";
import { fromMgrs, toMgrs } from "./js/mgrs.js";
import { pageValues } from "./js/manifest.js";
import { fillPdf } from "./js/pdfFill.js";
import { flightMinutes } from "./js/timeline.js";

const [lat, lon] = fromMgrs("12R WV 03141 68742");
const grid = toMgrs(lat, lon);
if (!grid.startsWith("12R WV")) throw new Error(`mgrs roundtrip ${grid}`);
if (flightMinutes(60) !== 20) throw new Error("flight minutes");

const person = { rank: "SGT", lastName: "Lister", lastFour: "1234", squad: "2-1" };
const key = "SGT|Lister|1234";
const mission = {
  missionDate: "2026-08-24",
  submittedDate: "2026-08-24",
  unit: "Baker/1-506IN/1MBDE",
  pocName: "1LT Greene",
  pocPhone: "617-775-2674",
  pocEmail: "nathaniel.greene37.mil@army.mil",
  reviewerName: "1LT Deona Roberts",
  reviewerEmail: "deona.l.roberts.mil@army.mil",
  statement: "statement",
  trainingIntent: "intent",
  task1: "T",
  purpose1: "P",
  description: "Move squad.",
  remarks: "N/A",
  timelineDirty: true,
  timeline: [
    { date: "2026-08-24", localTime: "1400", event: "DEPART LZ APACHE", location: "12R XX 00000 00000" },
    { date: "2026-08-24", localTime: "1430", event: "ARRIVE LZ CALI", location: "12R XX 00000 00000" },
  ],
  legs: [
    { start: "LZ APACHE", end: "LZ CALI", pax: [key] },
    { start: "LZ CALI", end: "LZ BAKER", pax: [] },
  ],
};
const people = { [key]: person };
const pages = pageValues(mission, people);
if (pages[0]["Last NameRow1"] !== "Lister") throw new Error("pax row");
if (pages[0]["Last NameRow2"] !== "NO TROOPS") throw new Error("no troops");
if (pages[0]["PickUp LocationRow2"] !== "LZ CALI") throw new Error("pickup");

const packet = buildFieldValues(mission, { "LZ APACHE": "12R XX 00000 00000", "LZ CALI": "12R YY 00000 00000" }, people);
const template = readFileSync(new URL("./assets/template.pdf", import.meta.url));
const filled = await fillPdf(template, packet);
const doc = await PDFDocument.load(filled);
const form = doc.getForm();
const last = form.getTextField("Last NameRow1").getText();
if (last !== "Lister") throw new Error(`pdf last name ${last}`);
const unit = form.getTextField("Supported Unit").getText();
if (!unit.includes("Baker")) throw new Error(`unit ${unit}`);
console.log("web check ok", doc.getPageCount());
