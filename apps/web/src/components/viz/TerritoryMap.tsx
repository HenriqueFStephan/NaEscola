"use client";

import { useEffect, useMemo, useState } from "react";
import { API_URL } from "@/lib/api";
import { project, ringPath, type MapView } from "@/lib/geo/project";
import { useReducedMotion } from "./useReducedMotion";

type Feature = {
  properties: { name: string; borderPrecision: number };
  geometry: { type: string; coordinates: number[][][][] };
};

type Collection = {
  features: Feature[];
  naescola: { view: MapView };
};

type Narrative = { stateId: string; title: string; text: string };

const PALETTE = ["#0e5c57", "#8d4528", "#1d4e89", "#6b3f69", "#8a6a2f", "#3d6b3a", "#8c3d4e", "#3f5e6b"];

function colorFor(name: string): string {
  if (name === "Eastern Roman Empire") return "#1d4e89";
  if (["Rome", "Roman Republic", "Roman Empire", "Western Roman Empire"].includes(name)) return "#8d4528";
  if (name === "Empire of Alexander") return "#0e5c57";
  let hash = 0;
  for (const char of name) hash = (hash * 31 + char.charCodeAt(0)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

export function TerritoryMap({ config, description }: { config: Record<string, unknown>; description: string }) {
  const stateIds = config.stateIds as string[];
  const narratives = config.narratives as Narrative[];
  const focus = new Set(config.focusNames as string[]);
  const [docs, setDocs] = useState<Record<string, Collection>>({});
  const [glosses, setGlosses] = useState<Record<string, string>>({});
  const [index, setIndex] = useState(0);
  const [outgoing, setOutgoing] = useState<number | null>(null);
  const [outgoingOpacity, setOutgoingOpacity] = useState(1);
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
      setIndex((current) => {
        setOutgoing(reduced ? null : current);
        return (current + 1) % stateIds.length;
      });
    }, reduced ? 1600 : 2800);
    return () => window.clearInterval(timer);
  }, [playing, reduced, stateIds.length]);

  useEffect(() => {
    if (outgoing === null || reduced) return undefined;
    setOutgoingOpacity(1);
    const frame = window.requestAnimationFrame(() => setOutgoingOpacity(0));
    const timer = window.setTimeout(() => setOutgoing(null), 480);
    return () => {
      window.cancelAnimationFrame(frame);
      window.clearTimeout(timer);
    };
  }, [outgoing, reduced]);

  const currentId = stateIds[index];
  const narrative = narratives.find((item) => item.stateId === currentId);
  const view = docs[currentId]?.naescola.view;
  const names = useMemo(() => {
    const features = docs[currentId]?.features ?? [];
    return [...new Set(features.map((feature) => feature.properties.name))].sort((a, b) => a.localeCompare(b, "pt"));
  }, [docs, currentId]);

  function go(next: number) {
    const wrapped = (next + stateIds.length) % stateIds.length;
    setOutgoing(reduced ? null : index);
    setIndex(wrapped);
  }

  function draw(stateIndex: number, opacity: number) {
    const document = docs[stateIds[stateIndex]];
    if (!document || !view) return null;
    return document.features.map((feature, featureIndex) => {
      const name = feature.properties.name;
      const active = selected === name;
      return (
        <path
          key={`${stateIndex}-${featureIndex}`}
          d={feature.geometry.coordinates.map((polygon) => polygon.map((ring) => ringPath(ring, view, 800, 460)).join(" ")).join(" ")}
          fill={colorFor(name)}
          fillOpacity={active ? 0.85 : 0.55}
          stroke="#1c2430"
          strokeDasharray="4 3"
          strokeWidth={active ? 1.6 : 0.8}
          opacity={opacity}
          onClick={() => setSelected(name)}
        >
          <title>{glosses[name] ?? name}</title>
        </path>
      );
    });
  }

  function labels() {
    const document = docs[currentId];
    if (!document || !view) return null;
    return document.features.filter((feature) => focus.has(feature.properties.name) || feature.properties.name === selected).map((feature) => {
      const points = feature.geometry.coordinates.flat(2).filter((point) => point[0] >= view.minLon && point[0] <= view.maxLon && point[1] >= view.minLat && point[1] <= view.maxLat);
      if (points.length === 0) return null;
      const lon = points.reduce((sum, point) => sum + point[0], 0) / points.length;
      const lat = points.reduce((sum, point) => sum + point[1], 0) / points.length;
      const [x, y] = project(lon, lat, view, 800, 460);
      const name = feature.properties.name;
      return <text key={name} x={x} y={y} textAnchor="middle" fontSize="13" fill="#1c2430">{glosses[name] ?? name}</text>;
    });
  }

  return (
    <figure className="viz">
      <div className="controls">
        <button type="button" onClick={() => setPlaying((value) => !value)}>{playing ? "Pausar" : "Reproduzir"}</button>
        <button type="button" className="secondary" onClick={() => go(index - 1)}>Anterior</button>
        <button type="button" className="secondary" onClick={() => go(index + 1)}>Próximo</button>
        <button type="button" className="secondary" onClick={() => { setPlaying(false); setOutgoing(null); setIndex(0); setSelected(null); }}>Restaurar</button>
      </div>
      <label>
        Ano do recorte
        <input
          type="range"
          min={0}
          max={stateIds.length - 1}
          step={1}
          value={index}
          aria-valuetext={narrative?.title ?? currentId}
          onChange={(event) => go(Number(event.target.value))}
        />
      </label>
      {error ? <p role="alert">{error}</p> : null}
      <div className="map-layout">
        <svg viewBox="0 0 800 460" role="img" aria-label={description}>
          <rect width="800" height="460" fill="#f7f1e4" />
          <g style={{ opacity: outgoing === null || reduced ? 1 : 0.2 + outgoingOpacity * 0.8, transition: reduced ? undefined : "opacity 180ms linear" }}>{draw(index, 1)}</g>
          {labels()}
        </svg>
        <div>
          <p className="live" aria-live="polite"><strong>{narrative?.title}</strong> {narrative?.text}</p>
          <p>Linha tracejada: reconstrução aproximada, precisão 1 no conjunto de origem. Não há costa separada.</p>
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
      <ol>
        {narratives.map((item, itemIndex) => (
          <li key={item.stateId}>
            <button type="button" className="secondary" aria-current={itemIndex === index} onClick={() => go(itemIndex)}>{item.title}</button>
          </li>
        ))}
      </ol>
    </figure>
  );
}
