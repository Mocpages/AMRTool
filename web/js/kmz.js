import { unzipSync } from "../vendor/fflate.esm.js";
import { ARF_LZ_NAME, EXTRA_LANDING_ZONES } from "./defaults.js";
import { fromMgrs, toMgrs } from "./mgrs.js";

export async function zonesFromKmz(buffer) {
  const xml = kmlText(new Uint8Array(buffer));
  const fromKmz = placemarks(xml).map(placemarkToZone).filter(Boolean);
  return withVirtual(withExtras(fromKmz)).sort((a, b) => a.name.localeCompare(b.name));
}

function kmlText(bytes) {
  const files = unzipSync(bytes);
  const name = Object.keys(files).find((key) => key.toLowerCase().endsWith(".kml"));
  if (!name) throw new Error("no KML inside KMZ");
  return new TextDecoder().decode(files[name]);
}

function placemarks(xml) {
  const doc = new DOMParser().parseFromString(xml, "text/xml");
  return [...doc.getElementsByTagName("*")].filter((el) => el.localName === "Placemark");
}

function placemarkToZone(mark) {
  const name = childText(mark, "name").trim();
  if (!name.toUpperCase().startsWith("LZ ")) return null;
  const coords = nestedText(mark, "coordinates").trim();
  if (!coords) return null;
  const [lonText, latText] = coords.split(",");
  const lon = Number(lonText);
  const lat = Number(latText);
  return { name, lon, lat, mgrs: toMgrs(lat, lon) };
}

function childText(el, local) {
  const child = [...el.children].find((node) => node.localName === local);
  return child ? child.textContent || "" : "";
}

function nestedText(el, local) {
  const node = [...el.getElementsByTagName("*")].find((item) => item.localName === local);
  return node ? node.textContent || "" : "";
}

function withExtras(zones) {
  const known = new Set(zones.map((zone) => zone.name.toUpperCase()));
  const extras = EXTRA_LANDING_ZONES.filter(([name]) => !known.has(name.toUpperCase()));
  return [...zones, ...extras.map(extraZone)];
}

function extraZone([name, mgrs]) {
  const [lat, lon] = fromMgrs(mgrs);
  return { name, lon, lat, mgrs };
}

function withVirtual(zones) {
  const known = new Set(zones.map((zone) => zone.name.toUpperCase()));
  if (known.has(ARF_LZ_NAME)) return zones;
  return [...zones, { name: ARF_LZ_NAME, lon: 0, lat: 0, mgrs: "" }];
}
