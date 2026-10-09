import { isArfLz, touchesArf } from "./defaults.js";
import { paddedBbox, project } from "./proj.js";

const MAP_W = 900;
const MAP_H = 872;

export async function overviewJpeg(zones, legs, fetchExtent) {
  const used = usedZones(zones, legs);
  if (!used.length) return null;
  const bbox = paddedBbox(used, MAP_W, MAP_H);
  const base = await fetchExtent(bbox, MAP_W, MAP_H);
  const canvas = document.createElement("canvas");
  canvas.width = MAP_W;
  canvas.height = MAP_H;
  const ctx = canvas.getContext("2d");
  if (base) ctx.drawImage(base, 0, 0, MAP_W, MAP_H);
  else {
    ctx.fillStyle = "#c8b89a";
    ctx.fillRect(0, 0, MAP_W, MAP_H);
  }
  drawRoutes(ctx, used, legs, bbox);
  return canvasToJpeg(canvas);
}

function usedZones(zones, legs) {
  const byName = Object.fromEntries(zones.map((zone) => [zone.name, zone]));
  const seen = new Set();
  const used = [];
  for (const leg of legs) {
    if (touchesArf(leg.start, leg.end)) continue;
    for (const name of [leg.start, leg.end]) {
      const zone = byName[name];
      if (!name || isArfLz(name) || seen.has(name) || !zone) continue;
      seen.add(name);
      used.push(zone);
    }
  }
  return used;
}

function drawRoutes(ctx, zones, legs, bbox) {
  const points = zones.map((zone) => project(bbox, MAP_W, MAP_H, zone.lon, zone.lat));
  const routes = legPixels(legs, zones, bbox);
  for (const route of routes) drawArrow(ctx, route.start, route.end);
  zones.forEach((zone, index) => drawZone(ctx, points[index], zone.name));
  for (const route of routes) {
    drawLabel(ctx, midpoint(route.start, route.end), `Leg ${route.label}`, 22);
  }
}

function legPixels(legs, zones, bbox) {
  const byName = Object.fromEntries(zones.map((zone) => [zone.name, zone]));
  const groups = new Map();
  const order = [];
  legs.forEach((leg, index) => {
    if (touchesArf(leg.start, leg.end)) return;
    const start = byName[leg.start];
    const end = byName[leg.end];
    if (!start || !end) return;
    const key = `${leg.start}\0${leg.end}`;
    if (!groups.has(key)) {
      groups.set(key, []);
      order.push(key);
    }
    groups.get(key).push(index + 1);
  });
  return order.map((key) => {
    const [startName, endName] = key.split("\0");
    return {
      label: groups.get(key).join(","),
      start: project(bbox, MAP_W, MAP_H, byName[startName].lon, byName[startName].lat),
      end: project(bbox, MAP_W, MAP_H, byName[endName].lon, byName[endName].lat),
    };
  });
}

function drawZone(ctx, point, name) {
  const left = point[0] < MAP_W / 2;
  const origin = left ? [point[0] - 150, point[1] - 16] : [point[0] + 16, point[1] - 16];
  haloLine(ctx, [origin[0] + (left ? 140 : 0), origin[1] + 12], point, 3);
  ctx.fillStyle = "#fff";
  ctx.beginPath();
  ctx.arc(point[0], point[1], 11, 0, Math.PI * 2);
  ctx.fill();
  ctx.fillStyle = "#000";
  ctx.beginPath();
  ctx.arc(point[0], point[1], 8, 0, Math.PI * 2);
  ctx.fill();
  drawLabel(ctx, origin, name, 18);
}

function drawLabel(ctx, origin, text, size) {
  ctx.font = `700 ${size}px Arial, sans-serif`;
  ctx.lineWidth = 4;
  ctx.strokeStyle = "#fff";
  ctx.fillStyle = "#000";
  ctx.strokeText(text, origin[0], origin[1]);
  ctx.fillText(text, origin[0], origin[1]);
}

function drawArrow(ctx, start, end) {
  const scale = MAP_W / 1648;
  const stem = 48 * scale;
  const trimmed = shorten(start, end, 14 * scale, 22 * scale);
  if (!trimmed) return;
  const [a, tip] = trimmed;
  const [ux, uy] = unit(a, tip);
  const px = -uy;
  const py = ux;
  const headLen = stem * (2 / 3);
  const stemLen = Math.hypot(tip[0] - a[0], tip[1] - a[1]) - headLen;
  if (stemLen < 12 * scale) return;
  const segments = arrowSegments(a, tip, ux, uy, px, py, stem, headLen);
  strokeAll(ctx, segments, Math.max(4, 11 * scale), "#fff");
  strokeAll(ctx, segments, Math.max(2, 6 * scale), "#000");
}

function arrowSegments(a, tip, ux, uy, px, py, stem, headLen) {
  const base = [tip[0] - ux * headLen, tip[1] - uy * headLen];
  const half = stem / 2;
  const headHalf = stem;
  const sHi = [a[0] + px * half, a[1] + py * half];
  const sLo = [a[0] - px * half, a[1] - py * half];
  const eHi = [base[0] + px * half, base[1] + py * half];
  const eLo = [base[0] - px * half, base[1] - py * half];
  const left = [base[0] + px * headHalf, base[1] + py * headHalf];
  const right = [base[0] - px * headHalf, base[1] - py * headHalf];
  return [[sHi, eLo], [sLo, eHi], [eHi, left], [eLo, right], [left, tip], [tip, right]];
}

function strokeAll(ctx, segments, width, color) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineCap = "round";
  for (const [a, b] of segments) {
    ctx.beginPath();
    ctx.moveTo(a[0], a[1]);
    ctx.lineTo(b[0], b[1]);
    ctx.stroke();
  }
}

function shorten(start, end, startPad, endPad) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const length = Math.hypot(dx, dy);
  if (length < startPad + endPad + 8) return null;
  const ux = dx / length;
  const uy = dy / length;
  return [
    [start[0] + ux * startPad, start[1] + uy * startPad],
    [end[0] - ux * endPad, end[1] - uy * endPad],
  ];
}

function unit(start, end) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const length = Math.hypot(dx, dy) || 1;
  return [dx / length, dy / length];
}

function midpoint(a, b) {
  return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 8];
}

function haloLine(ctx, start, end, width) {
  strokeAll(ctx, [[start, end]], width + 6, "#fff");
  strokeAll(ctx, [[start, end]], width, "#000");
}

function canvasToJpeg(canvas) {
  return new Promise((resolve) => {
    canvas.toBlob((blob) => {
      blob.arrayBuffer().then((buf) => resolve(new Uint8Array(buf)));
    }, "image/jpeg", 0.9);
  });
}
