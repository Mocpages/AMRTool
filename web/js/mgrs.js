const WGS84_A = 6378137.0;
const WGS84_E2 = 6.6943799901413165e-3;
const UTM_K0 = 0.9996;
const UTM_E0 = 500000.0;
const LAT_BANDS = "CDEFGHJKLMNPQRSTUVWX";
const COL_SETS = ["ABCDEFGH", "JKLMNPQR", "STUVWXYZ"];
const ROW_LETTERS = "ABCDEFGHJKLMNPQRSTUV";

export function fromMgrs(text) {
  const parsed = parseMgrs(text);
  const easting = squareEasting(parsed.zone, parsed.col) + parsed.eastM + 0.5;
  const northing = squareNorthing(parsed) + parsed.northM + 0.5;
  return utmToLatLon(parsed.zone, easting, northing, isSouth(parsed.band));
}

export function toMgrs(lat, lon) {
  const utm = latLonToUtm(lat, lon);
  const band = latitudeBand(lat);
  const col = colLetter(utm.zone, utm.easting);
  const row = rowLetter(utm.zone, utm.northing);
  const east = Math.trunc(utm.easting) % 100000;
  const north = Math.trunc(utm.northing) % 100000;
  const eText = String(east).padStart(5, "0");
  const nText = String(north).padStart(5, "0");
  return `${String(utm.zone).padStart(2, "0")}${band} ${col}${row} ${eText} ${nText}`;
}

function latitudeBand(lat) {
  if (lat < -80 || lat > 84) throw new Error(`latitude ${lat} is outside MGRS range`);
  if (lat >= 72) return "X";
  return LAT_BANDS[Math.trunc((lat + 80) / 8)];
}

function colLetter(zone, easting) {
  const letters = COL_SETS[(zone - 1) % 3];
  const col = Math.trunc(easting / 100000) - 1;
  if (col < 0 || col >= letters.length) throw new Error("easting is outside the UTM 100 km grid");
  return letters[col];
}

function rowLetter(zone, northing) {
  let idx = Math.trunc(northing / 100000) % 20;
  if (zone % 2 === 0) idx = (idx + 5) % 20;
  return ROW_LETTERS[idx];
}

function latLonToUtm(lat, lon) {
  const zone = Math.trunc((lon + 180) / 6) + 1;
  const lon0 = ((zone - 1) * 6 - 180 + 3) * Math.PI / 180;
  const en = utmEn(lat * Math.PI / 180, lon * Math.PI / 180, lon0);
  const northing = lat < 0 ? en.northing + 10000000 : en.northing;
  return { zone, easting: en.easting, northing };
}

function utmEn(latRad, lonRad, lon0) {
  const ep2 = WGS84_E2 / (1 - WGS84_E2);
  const sinLat = Math.sin(latRad);
  const cosLat = Math.cos(latRad);
  const n = WGS84_A / Math.sqrt(1 - WGS84_E2 * sinLat * sinLat);
  const t = Math.tan(latRad) ** 2;
  const c = ep2 * cosLat * cosLat;
  const a = cosLat * (lonRad - lon0);
  return {
    easting: eastingOf(n, t, c, a, ep2),
    northing: northingOf(meridianArc(latRad), n, latRad, t, c, a, ep2),
  };
}

function meridianArc(latRad) {
  const e2 = WGS84_E2;
  const e4 = e2 * e2;
  const e6 = e4 * e2;
  return WGS84_A * (
    (1 - e2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * latRad
    - (3 * e2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * Math.sin(2 * latRad)
    + (15 * e4 / 256 + 45 * e6 / 1024) * Math.sin(4 * latRad)
    - (35 * e6 / 3072) * Math.sin(6 * latRad)
  );
}

function eastingOf(n, t, c, a, ep2) {
  const a3 = a ** 3;
  const a5 = a ** 5;
  let term = a + (1 - t + c) * a3 / 6;
  term += (5 - 18 * t + t * t + 72 * c - 58 * ep2) * a5 / 120;
  return UTM_K0 * n * term + UTM_E0;
}

function northingOf(m, n, latRad, t, c, a, ep2) {
  const a2 = a ** 2;
  const a4 = a ** 4;
  const a6 = a ** 6;
  let term = a2 / 2 + (5 - t + 9 * c + 4 * c * c) * a4 / 24;
  term += (61 - 58 * t + t * t + 600 * c - 330 * ep2) * a6 / 720;
  return UTM_K0 * (m + n * Math.tan(latRad) * term);
}

function parseMgrs(text) {
  const compact = [...text.toUpperCase()].filter((ch) => /[A-Z0-9]/.test(ch)).join("");
  if (compact.length < 7) throw new Error(`invalid MGRS: ${text}`);
  const digits = compact.slice(5);
  if (digits.length % 2) throw new Error(`invalid MGRS digits: ${text}`);
  const half = digits.length / 2;
  return {
    zone: Number(compact.slice(0, 2)),
    band: compact[2],
    col: compact[3],
    row: compact[4],
    eastM: Number(digits.slice(0, half).padEnd(5, "0").slice(0, 5)),
    northM: Number(digits.slice(half).padEnd(5, "0").slice(0, 5)),
  };
}

function squareEasting(zone, colLetter) {
  const letters = COL_SETS[(zone - 1) % 3];
  return (letters.indexOf(colLetter) + 1) * 100000;
}

function squareNorthing(parsed) {
  const target = ROW_LETTERS.indexOf(parsed.row);
  const limits = bandLimits(parsed.band);
  for (let cycle = 0; cycle < 100; cycle += 1) {
    if (rowIndex(parsed.zone, cycle) !== target) continue;
    const base = cycle * 100000;
    const [lat] = utmToLatLon(parsed.zone, UTM_E0, base + 50000, isSouth(parsed.band));
    if (lat >= limits[0] && lat < limits[1]) return base;
  }
  throw new Error(`no 100 km row ${parsed.row} in band ${parsed.band}`);
}

function rowIndex(zone, cycle) {
  let idx = cycle % 20;
  if (zone % 2 === 0) idx = (idx + 5) % 20;
  return idx;
}

function bandLimits(band) {
  if (band === "X") return [72, 84.1];
  const idx = LAT_BANDS.indexOf(band);
  const south = -80 + idx * 8;
  return [south, south + 8];
}

function isSouth(band) {
  return LAT_BANDS.indexOf(band) < LAT_BANDS.indexOf("N");
}

function utmToLatLon(zone, easting, northing, southern) {
  const north = southern ? northing - 10000000 : northing;
  const x = easting - UTM_E0;
  const ep2 = WGS84_E2 / (1 - WGS84_E2);
  const m = north / UTM_K0;
  const denom = WGS84_A * (1 - WGS84_E2 / 4 - 3 * WGS84_E2 ** 2 / 64 - 5 * WGS84_E2 ** 3 / 256);
  const fp = footprintLat(m / denom, WGS84_E2);
  const lat = utmLat(x, fp, WGS84_E2, ep2);
  const lon = utmLon(x, fp, WGS84_E2, ep2);
  const lon0 = ((zone - 1) * 6 - 180 + 3) * Math.PI / 180;
  return [lat * 180 / Math.PI, (lon0 + lon) * 180 / Math.PI];
}

function footprintLat(mu, e2) {
  const e1 = (1 - Math.sqrt(1 - e2)) / (1 + Math.sqrt(1 - e2));
  return (
    mu
    + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * Math.sin(2 * mu)
    + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * Math.sin(4 * mu)
    + (151 * e1 ** 3 / 96) * Math.sin(6 * mu)
  );
}

function utmLon(x, fp, e2, ep2) {
  const sinFp = Math.sin(fp);
  const cosFp = Math.cos(fp);
  const n1 = WGS84_A / Math.sqrt(1 - e2 * sinFp * sinFp);
  const t1 = Math.tan(fp) ** 2;
  const c1 = ep2 * cosFp * cosFp;
  const d = x / (n1 * UTM_K0);
  let term = d - (1 + 2 * t1 + c1) * d ** 3 / 6;
  term += (5 - 2 * c1 + 28 * t1 - 3 * c1 ** 2 + 8 * ep2 + 24 * t1 ** 2) * d ** 5 / 120;
  return term / cosFp;
}

function utmLat(x, fp, e2, ep2) {
  const sinFp = Math.sin(fp);
  const cosFp = Math.cos(fp);
  const tanFp = Math.tan(fp);
  const n1 = WGS84_A / Math.sqrt(1 - e2 * sinFp * sinFp);
  const t1 = tanFp * tanFp;
  const c1 = ep2 * cosFp * cosFp;
  const r1 = WGS84_A * (1 - e2) / (1 - e2 * sinFp * sinFp) ** 1.5;
  const d = x / (n1 * UTM_K0);
  let term = d ** 2 / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * ep2) * d ** 4 / 24;
  term += (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * ep2 - 3 * c1 * c1) * d ** 6 / 720;
  return fp - (n1 * tanFp / r1) * term;
}
