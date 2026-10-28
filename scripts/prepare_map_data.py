#!/usr/bin/env python3
"""Filter historical-basemaps snapshots to the Mediterranean window.

The output keeps dataset names, years, and BORDERPRECISION. Coordinates are
rounded to three decimal degrees for display size. Rounding does not create
intermediate borders: each file remains one documented snapshot. Features are
included only when at least 20% of their vertices fall inside the window, so
global polygons are not pasted across the lesson map.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path("/tmp/naescola-sources")
OUT_DIR = ROOT / "content/maps/mediterranean"
VIEW = (-12.0, 24.0, 48.0, 54.0)  # min lon, min lat, max lon, max lat
YEARS = {
    "bc323": {"filename": "world_bc323.geojson", "label": "323 AEC", "sort": -323},
    "bc200": {"filename": "world_bc200.geojson", "label": "200 AEC", "sort": -200},
    "bc100": {"filename": "world_bc100.geojson", "label": "100 AEC", "sort": -100},
    "ce100": {"filename": "world_100.geojson", "label": "100 EC", "sort": 100},
    "ce200": {"filename": "world_200.geojson", "label": "200 EC", "sort": 200},
    "ce400": {"filename": "world_400.geojson", "label": "400 EC", "sort": 400},
}
SOURCE_COMMIT = "da7a4b735ecef70aebdc9c73e409d8a2500d50f3"


def round_coords(value):
    if isinstance(value, list):
        if value and isinstance(value[0], (int, float)):
            return [round(float(value[0]), 3), round(float(value[1]), 3)]
        return [round_coords(item) for item in value]
    raise TypeError(type(value))


def vertex_ratio(geometry: dict) -> float:
    inside = 0
    total = 0

    def walk(coords) -> None:
        nonlocal inside, total
        if coords and isinstance(coords[0], (int, float)):
            total += 1
            lon, lat = coords[0], coords[1]
            if VIEW[0] <= lon <= VIEW[2] and VIEW[1] <= lat <= VIEW[3]:
                inside += 1
            return
        for item in coords:
            walk(item)

    walk(geometry["coordinates"])
    return (inside / total) if total else 0.0


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_states = []
    for state_id, meta in YEARS.items():
        source = SOURCE_DIR / meta["filename"]
        if not source.exists():
            raise SystemExit(f"Missing source {source}. Download it before regenerating.")
        document = json.loads(source.read_text(encoding="utf-8"))
        kept = []
        for feature in document["features"]:
            props = feature.get("properties") or {}
            name = (props.get("NAME") or "").strip()
            if not name or name == "?":
                continue
            ratio = vertex_ratio(feature["geometry"])
            if ratio < 0.2:
                continue
            kept.append(
                {
                    "type": "Feature",
                    "properties": {
                        "name": name,
                        "subjecto": props.get("SUBJECTO"),
                        "partOf": props.get("PARTOF"),
                        "borderPrecision": props.get("BORDERPRECISION"),
                        "vertexRatioInView": round(ratio, 3),
                    },
                    "geometry": {
                        "type": feature["geometry"]["type"],
                        "coordinates": round_coords(feature["geometry"]["coordinates"]),
                    },
                }
            )
        if not kept:
            raise SystemExit(f"No features kept for {state_id}")
        collection = {
            "type": "FeatureCollection",
            "name": state_id,
            "features": kept,
            "naescola": {
                "sourceRepository": "https://github.com/aourednik/historical-basemaps",
                "sourceCommit": SOURCE_COMMIT,
                "sourceFile": meta["filename"],
                "license": "GPL-3.0",
                "view": {"minLon": VIEW[0], "minLat": VIEW[1], "maxLon": VIEW[2], "maxLat": VIEW[3]},
                "coordinateRoundingDecimalDegrees": 3,
                "inclusionRule": "At least 20% of vertices inside the view. No border was interpolated.",
                "uncertainty": "BORDERPRECISION 1 means the upstream dataset marks the boundary as approximate.",
            },
        }
        (OUT_DIR / f"{state_id}.geojson").write_text(
            json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        manifest_states.append(
            {
                "id": state_id,
                "label": meta["label"],
                "sort": meta["sort"],
                "featureCount": len(kept),
                "file": f"{state_id}.geojson",
            }
        )
        print(state_id, len(kept))
    manifest = {
        "datasetId": "mediterranean-reconstructions-v1",
        "sourceCommit": SOURCE_COMMIT,
        "license": "GPL-3.0",
        "states": manifest_states,
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
