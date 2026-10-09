import {
  PDFDocument,
  StandardFonts,
} from "../vendor/pdf-lib.esm.min.js";
import { MANIFEST_PAGE } from "./defaults.js";

const OVERVIEW_SLOT = "Image2_af_image";
const CHIP_SLOTS = ["Image13_af_image", "Image14_af_image", "Image15_af_image"];
const HEADER_FIELDS = [
  "Supported Unit POC",
  "Supported Unit POC Email",
  "Supported Unit POC Phone",
  "Supporting Unit POC",
  "Supporting Unit POC Email",
  "Supporting Unit POC Phone",
];
const ROW_FIELD = /^(?:Rank|Last Name|Nationality|Service|Last 4 IDSSN|PickUp Location|DropOff Location|\d+)Row\d+$/;

export async function fillPdf(templateBytes, packet) {
  const pdf = await PDFDocument.load(templateBytes);
  const form = pdf.getForm();
  const font = await pdf.embedFont(StandardFonts.Helvetica);
  applyValues(form, { ...packet.values, ...packet.firstPage });
  paintFields(form, font);
  await embedOverview(pdf, form, packet.overview);
  await embedChips(pdf, form, packet.chips || []);
  await appendOverflow(pdf, templateBytes, packet.extraManifest || [], packet.values);
  return pdf.save();
}

function applyValues(form, values) {
  for (const field of form.getFields()) {
    const name = field.getName();
    if (!(name in values)) continue;
    try {
      setFieldValue(field, values[name]);
    } catch (err) {
      console.warn(`skip field ${name}`, err);
    }
  }
}

function setFieldValue(field, value) {
  if (value === false && field.uncheck) {
    field.uncheck();
    return;
  }
  if (value === true && field.check) {
    field.check();
    return;
  }
  if (field.setText) {
    field.setText(String(value ?? ""));
    return;
  }
  if (field.select) field.select(String(value));
}

function paintFields(form, font) {
  for (const field of form.getFields()) {
    try {
      field.updateAppearances(font);
    } catch {
      /* buttons and some radios have no text appearance */
    }
  }
}

async function embedOverview(pdf, form, bytes) {
  if (!bytes) return;
  await drawInSlot(pdf, form, OVERVIEW_SLOT, bytes);
}

async function embedChips(pdf, form, chips) {
  for (let index = 0; index < chips.length && index < CHIP_SLOTS.length; index += 1) {
    await drawInSlot(pdf, form, CHIP_SLOTS[index], chips[index]);
  }
}

async function drawInSlot(pdf, form, name, bytes) {
  const placed = takeSlot(pdf, form, name);
  if (!placed) return;
  const image = await pdf.embedJpg(bytes);
  const box = fitBox(placed.rect, image.width, image.height);
  placed.page.drawImage(image, box);
}

function takeSlot(pdf, form, name) {
  let field;
  try {
    field = form.getField(name);
  } catch {
    return null;
  }
  const widget = field.acroField.getWidgets()[0];
  if (!widget) return null;
  const rect = widget.getRectangle();
  const page = pageForWidget(pdf, widget);
  form.removeField(field);
  return { page, rect };
}

function pageForWidget(pdf, widget) {
  const ref = widget.P && widget.P();
  const pages = pdf.getPages();
  if (!ref) return pages[2];
  return pages.find((page) => page.ref === ref) || pages[2];
}

function fitBox(rect, imgW, imgH) {
  const scale = Math.min(rect.width / imgW, rect.height / imgH);
  const width = imgW * scale;
  const height = imgH * scale;
  return {
    x: rect.x + (rect.width - width) / 2,
    y: rect.y + (rect.height - height) / 2,
    width,
    height,
  };
}

async function appendOverflow(pdf, templateBytes, extras, values) {
  const headers = {};
  for (const name of HEADER_FIELDS) headers[name] = String(values[name] || "");
  for (const chunk of extras) {
    const baked = await bakeManifest(templateBytes, headers, chunk);
    const [page] = await pdf.copyPages(baked, [0]);
    pdf.addPage(page);
  }
}

async function bakeManifest(templateBytes, headers, chunk) {
  const source = await PDFDocument.load(templateBytes);
  const overflow = await PDFDocument.create();
  const [copied] = await overflow.copyPages(source, [MANIFEST_PAGE]);
  overflow.addPage(copied);
  const form = overflow.getForm();
  const font = await overflow.embedFont(StandardFonts.Helvetica);
  fillOverflow(form, { ...headers, ...chunk });
  paintFields(form, font);
  try {
    form.flatten();
  } catch (err) {
    console.warn("overflow flatten skipped", err);
  }
  return overflow;
}

function fillOverflow(form, combined) {
  for (const field of form.getFields()) {
    const name = field.getName();
    if (name in combined) setFieldValue(field, combined[name]);
    else if (ROW_FIELD.test(name)) setFieldValue(field, "");
  }
}
