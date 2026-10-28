export type MapView = {
  minLon: number;
  minLat: number;
  maxLon: number;
  maxLat: number;
};

export function project(lon: number, lat: number, view: MapView, width: number, height: number): [number, number] {
  const x = ((lon - view.minLon) / (view.maxLon - view.minLon)) * width;
  const y = ((view.maxLat - lat) / (view.maxLat - view.minLat)) * height;
  return [x, y];
}

export function ringPath(
  ring: number[][],
  view: MapView,
  width: number,
  height: number,
): string {
  return ring
    .map((point, index) => {
      const [x, y] = project(point[0], point[1], view, width, height);
      return `${index === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ") + " Z";
}
