const R = 6378137;
const MAX_LAT = 85.0511287798;

export function paddedBbox(zones, width, height, padFrac = 0.2) {
  const xs = zones.map((zone) => lonToX(zone.lon));
  const ys = zones.map((zone) => latToY(zone.lat));
  let minX = Math.min(...xs);
  let maxX = Math.max(...xs);
  let minY = Math.min(...ys);
  let maxY = Math.max(...ys);
  const padX = (maxX - minX) * padFrac || 2500;
  const padY = (maxY - minY) * padFrac || 2500;
  minX -= padX;
  maxX += padX;
  minY -= padY;
  maxY += padY;
  [minX, maxX, minY, maxY] = fitAspect(minX, maxX, minY, maxY, width / height);
  return [xToLon(minX), yToLat(minY), xToLon(maxX), yToLat(maxY)];
}

export function project(bbox, width, height, lon, lat) {
  const [west, south, east, north] = bbox;
  const x0 = lonToX(west);
  const y0 = latToY(south);
  const x1 = lonToX(east);
  const y1 = latToY(north);
  const x = (lonToX(lon) - x0) / (x1 - x0) * width;
  const y = (y1 - latToY(lat)) / (y1 - y0) * height;
  return [x, y];
}

function lonToX(lon) {
  return lon * Math.PI / 180 * R;
}

function latToY(lat) {
  const clamped = Math.max(Math.min(lat, MAX_LAT), -MAX_LAT);
  return R * Math.log(Math.tan(Math.PI / 4 + clamped * Math.PI / 360));
}

function xToLon(x) {
  return x / R * 180 / Math.PI;
}

function yToLat(y) {
  return (2 * Math.atan(Math.exp(y / R)) - Math.PI / 2) * 180 / Math.PI;
}

function fitAspect(minX, maxX, minY, maxY, aspect) {
  const spanX = maxX - minX;
  const spanY = maxY - minY;
  if (spanX / spanY < aspect) {
    const extra = (aspect * spanY - spanX) / 2;
    return [minX - extra, maxX + extra, minY, maxY];
  }
  const extra = (spanX / aspect - spanY) / 2;
  return [minX, maxX, minY - extra, maxY + extra];
}
