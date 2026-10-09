import { isArfLz } from "./defaults.js";
import { uniqueLzNames } from "./fields.js";

const EXPORT_URL =
  "https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export";
const METERS = 250;
const PIXELS = 512;

export function routeNames(mission) {
  return uniqueLzNames(mission).filter((name) => !isArfLz(name)).slice(0, 3);
}

export async function chipJpeg(zone) {
  const raw = await downloadExtent(chipBbox(zone.lat, zone.lon), PIXELS, PIXELS);
  return captionJpeg(raw, zone.name);
}

export async function fetchExtentImage(bbox, width, height) {
  try {
    const bytes = await downloadExtent(bbox, width, height);
    return await bytesToImage(bytes);
  } catch (err) {
    console.warn("overview imagery skipped", err);
    return null;
  }
}

export async function downloadExtent(bbox, width, height) {
  const [west, south, east, north] = bbox;
  const query = `${EXPORT_URL}?bbox=${west},${south},${east},${north}`
    + `&bboxSR=4326&imageSR=3857&size=${width},${height}&format=jpg&f=image`;
  const response = await fetch(query);
  if (!response.ok) throw new Error(`imagery HTTP ${response.status}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  if (bytes.length < 1000) throw new Error("satellite image response was empty");
  return bytes;
}

function chipBbox(lat, lon) {
  const half = METERS / 2;
  const dLat = half / 111320;
  const dLon = half / (111320 * Math.cos(lat * Math.PI / 180));
  return [lon - dLon, lat - dLat, lon + dLon, lat + dLat];
}

async function captionJpeg(raw, title) {
  const image = await bytesToImage(raw);
  const canvas = document.createElement("canvas");
  canvas.width = image.width;
  canvas.height = image.height;
  const ctx = canvas.getContext("2d");
  ctx.drawImage(image, 0, 0);
  const bar = Math.max(36, Math.floor(image.height / 9));
  ctx.fillStyle = "#000";
  ctx.fillRect(0, image.height - bar, image.width, bar);
  ctx.fillStyle = "#fff";
  ctx.font = `${Math.max(18, Math.floor(bar / 2))}px Arial, sans-serif`;
  const width = ctx.measureText(title).width;
  ctx.fillText(title, Math.max(8, (image.width - width) / 2), image.height - bar / 2 + 6);
  return new Promise((resolve) => {
    canvas.toBlob(async (blob) => {
      resolve(new Uint8Array(await blob.arrayBuffer()));
    }, "image/jpeg", 0.9);
  });
}

function bytesToImage(bytes) {
  return new Promise((resolve, reject) => {
    const blob = new Blob([bytes], { type: "image/jpeg" });
    const url = URL.createObjectURL(blob);
    const image = new Image();
    image.onload = () => {
      URL.revokeObjectURL(url);
      resolve(image);
    };
    image.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("could not decode satellite image"));
    };
    image.src = url;
  });
}
