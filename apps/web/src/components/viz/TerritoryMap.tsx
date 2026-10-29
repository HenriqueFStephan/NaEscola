"use client";

import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { project, ringPath, type MapView } from "@/lib/geo/project";
import { useReducedMotion } from "./useReducedMotion";

type Geometry = { type: string; coordinates: number[][][] | number[][][][] };

type Feature = {
  properties: { name: string; borderPrecision: number };
  geometry: Geometry;
};

type Collection = {
  features: Feature[];
  naescola: { view: MapView };
};

type Narrative = { stateId: string; title: string; text: string };

const PALETTE = ["#0e5c57", "#8d4528", "#1d4e89", "#6b3f69", "#8a6a2f", "#3d6b3a", "#8c3d4e", "#3f5e6b"];
const WIDTH = 800;
const HEIGHT = 460;

function colorFor(name: string): string {
  if (name === "Eastern Roman Empire") return "#1d4e89";
  if (["Rome", "Roman Republic", "Roman Empire", "Western Roman Empire"].includes(name)) return "#8d4528";
  if (name === "Empire of Alexander") return "#0e5c57";
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

function polygonsOf(geometry: Geometry): number[][][][] {
  if (geometry.type === "Polygon") return [geometry.coordinates as number[][][]];
  return geometry.coordinates as number[][][][];
}

function usableRing(ring: number[][]): boolean {
  const unique = new Set(ring.map((point) => `${point[0]},${point[1]}`));
  return unique.size >= 3;
}

export function TerritoryMap({ config, description }: { config: Record<string, unknown>; description: string }) {
  const stateIds = config.stateIds as string[];
  const narratives = config.narratives as Narrative[];
  const focus = new Set(config.focusNames as string[]);
  const [docs, setDocs] = useState<Record<string, Collection>>({});
  const [glosses, setGlosses] = useState<Record<string, string>>({});
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState("");
  const reduced = useReducedMotion();

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const glossResponse = await fetch(`${API_URL}/api/maps/mediterranean/glosses`);
        const glossJson = await glossResponse.json();
        const loaded = await Promise.all(stateIds.map(async (stateId) => {
          const response = await fetch(`${API_URL}/api/maps/mediterranean/${stateId}`);
          if (!response.ok) throw new Error(stateId);
          return [stateId, await response.json()] as const;
        }));
        if (!cancelled) {
          setGlosses(glossJson.labels ?? {});
          setDocs(Object.fromEntries(loaded));
        }
      } catch {
        if (!cancelled) setError("Não foi possível carregar os recortes do mapa.");
      }
    }
    void load();
    return () => { cancelled = true; };
  }, [stateIds]);

  useEffect(() => {
    if (!playing) return undefined;
    const timer = window.setInterval(() => {
      setIndex((current) => (current + 1) % stateIds.length);
    }, reduced ? 1600 : 2800);
    return () => window.clearInterval(timer);
  }, [playing, reduced, stateIds.length]);

  const currentId = stateIds[index];
  const narrative = narratives.find((item) => item.stateId === currentId);
  const document = docs[currentId];
  const view = document?.naescola.view;
  const names = useMemo(() => {
    const features = document?.features ?? [];
    return [...new Set(features.map((feature) => feature.properties.name))].sort((a, b) => a.localeCompare(b, "pt"));
  }, [document]);

  function go(next: number) {
    setIndex((next + stateIds.length) % stateIds.length);
  }

  function shapes() {
    if (!document || !view) return null;
    return document.features.map((feature, featureIndex) => {
      const name = feature.properties.name;
      const active = selected === name;
      const paths = polygonsOf(feature.geometry).map((polygon) => (
        polygon.filter(usableRing).map((ring) => ringPath(ring, view, WIDTH, HEIGHT)).join(" ")
      )).filter(Boolean);
      if (paths.length === 0) return null;
      return (
        <path
          key={`${currentId}-${featureIndex}`}
          d={paths.join(" ")}
          fill={colorFor(name)}
          fillRule="evenodd"
          fillOpacity={active ? 0.85 : 0.55}
          stroke="#1c2430"
          strokeDasharray="4 3"
          strokeWidth={active ? 1.6 : 0.8}
          onClick={() => setSelected(name)}
        >
          <title>{glosses[name] ?? name}</title>
        </path>
      );
    });
  }

  function labels() {
    if (!document || !view) return null;
    return document.features.map((feature, featureIndex) => {
      const name = feature.properties.name;
      if (!focus.has(name) && name !== selected) return null;
      const points = polygonsOf(feature.geometry)
        .flat(2)
        .filter((point) => point.length >= 2 && point[0] >= view.minLon && point[0] <= view.maxLon && point[1] >= view.minLat && point[1] <= view.maxLat);
      if (points.length < 3) return null;
      const lon = points.reduce((sum, point) => sum + point[0], 0) / points.length;
      const lat = points.reduce((sum, point) => sum + point[1], 0) / points.length;
      const [x, y] = project(lon, lat, view, WIDTH, HEIGHT);
      if (x < 12 || x > WIDTH - 12 || y < 16 || y > HEIGHT - 8) return null;
      return <text key={`${currentId}-${featureIndex}-${name}`} x={x} y={y} textAnchor="middle" fontSize="13" fill="#1c2430">{glosses[name] ?? name}</text>;
    });
  }

  return (
    <figure className="viz">
      <div className="controls">
        <button type="button" onClick={() => setPlaying((value) => !value)}>{playing ? "Pausar" : "Reproduzir"}</button>
        <button type="button" className="secondary" onClick={() => go(index - 1)}>Anterior</button>
        <button type="button" className="secondary" onClick={() => go(index + 1)}>Próximo</button>
        <button type="button" className="secondary" onClick={() => { setPlaying(false); setIndex(0); setSelected(null); }}>Restaurar</button>
      </div>
      <label>
        Recorte documentado
        <input
          type="range"
          min={0}
          max={Math.max(stateIds.length - 1, 0)}
          step={1}
          value={index}
          aria-valuetext={narrative?.title ?? currentId}
          onChange={(event) => go(Number(event.target.value))}
        />
      </label>
      <p>O controle só para nos recortes prontos. Não há desenho dos anos que ficam no meio, nem animação de fronteira.</p>
      {error ? <p role="alert">{error}</p> : null}
      <div className="map-layout">
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label={description}>
          <rect width={WIDTH} height={HEIGHT} fill="#f7f1e4" />
          <g>{shapes()}</g>
          {labels()}
        </svg>
        <div>
          <p className="live" aria-live="polite"><strong>{narrative?.title}</strong> {narrative?.text}</p>
          <p>Linha tracejada: reconstrução aproximada do conjunto de origem, com BORDERPRECISION 1. A janela corta o que fica fora do Mediterrâneo documentado. Não há costa separada.</p>
          <ul>
            {names.map((name) => (
              <li key={name}>
                <button type="button" className="legend-button" aria-pressed={selected === name} onClick={() => setSelected(name)}>
                  <span className="swatch" style={{ background: colorFor(name) }} />
                  {glosses[name] ? `${glosses[name]} (${name})` : name}
                </button>
              </li>
            ))}
          </ul>
        </div>
      </div>
      <ol className="state-list">
        {narratives.map((item, itemIndex) => (
          <li key={item.stateId}>
            <button type="button" className="secondary" aria-current={itemIndex === index} onClick={() => { setPlaying(false); go(itemIndex); }}>{item.title}</button>
          </li>
        ))}
      </ol>
    </figure>
  );
}
