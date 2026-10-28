"use client";

import { useMemo, useState } from "react";
import { arrayTotal, evaluate, samples, type FunctionFamily } from "@/lib/math/functions";

type Parameter = { label: string; min: number; max: number; step: number; default: number };

export function FunctionPlot({ config, description }: { config: Record<string, unknown>; description: string }) {
  const family = config.family as FunctionFamily;
  const specs = config.parameters as Record<string, Parameter>;
  const [values, setValues] = useState(() => Object.fromEntries(Object.entries(specs).map(([key, spec]) => [key, spec.default])));
  const xMin = config.xMin as number;
  const xMax = config.xMax as number;
  const points = samples(family, values, xMin, xMax, (config.samples as number) ?? 240);
  const ys = points.map((point) => point.y);
  const yMin = (config.yMin as number | null) ?? Math.min(...ys, 0) - 0.5;
  const yMax = (config.yMax as number | null) ?? Math.max(...ys, 0) + 0.5;
  const width = 640;
  const height = 360;
  const pad = 36;
  const sx = (x: number) => pad + ((x - xMin) / (xMax - xMin)) * (width - pad * 2);
  const sy = (y: number) => height - pad - ((y - yMin) / (yMax - yMin)) * (height - pad * 2);
  const path = points.map((point, index) => `${index === 0 ? "M" : "L"}${sx(point.x).toFixed(1)} ${sy(point.y).toFixed(1)}`).join(" ");
  const yAtZero = evaluate(family, values, 0);
  return (
    <figure className="viz">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={description}>
        {[0, 1, 2, 3, 4].map((step) => {
          const y = yMin + ((yMax - yMin) * step) / 4;
          return <line key={step} x1={pad} x2={width - pad} y1={sy(y)} y2={sy(y)} stroke="#e6dfd2" />;
        })}
        <line x1={pad} x2={width - pad} y1={sy(0)} y2={sy(0)} stroke="#1c2430" />
        <line x1={sx(0)} x2={sx(0)} y1={pad} y2={height - pad} stroke="#1c2430" />
        <path d={path} fill="none" stroke="#0e5c57" strokeWidth="2.5" />
        <text x={width - pad} y={height - 8} textAnchor="end" fontSize="14">{String(config.xLabel)}</text>
        <text x={8} y={20} fontSize="14">{String(config.yLabel)}</text>
      </svg>
      <div className="controls">
        {Object.entries(specs).map(([key, spec]) => (
          <label key={key}>
            {spec.label}: {values[key]}
            <input
              type="range"
              min={spec.min}
              max={spec.max}
              step={spec.step}
              value={values[key]}
              aria-valuetext={`${spec.label} ${values[key]}`}
              onChange={(event) => setValues((current) => ({ ...current, [key]: Number(event.target.value) }))}
            />
          </label>
        ))}
        <button type="button" className="secondary" onClick={() => setValues(Object.fromEntries(Object.entries(specs).map(([key, spec]) => [key, spec.default])))}>
          Restaurar
        </button>
      </div>
      <p className="live" aria-live="polite">Em x = 0, y = {yAtZero.toFixed(2)}.</p>
    </figure>
  );
}

export function NumberLine({ config, description }: { config: Record<string, unknown>; description: string }) {
  const min = config.min as number;
  const max = config.max as number;
  const [value, setValue] = useState(config.initial as number);
  const markers = config.markers as Array<{ value: number; label: string }>;
  const x = (item: number) => 40 + ((item - min) / (max - min)) * 560;
  return (
    <figure className="viz">
      <svg viewBox="0 0 640 140" role="img" aria-label={description}>
        <line x1="40" x2="600" y1="70" y2="70" stroke="#1c2430" strokeWidth="2" />
        {(config.ticks as number[]).map((tick) => (
          <g key={tick}>
            <line x1={x(tick)} x2={x(tick)} y1="62" y2="78" stroke="#1c2430" />
            <text x={x(tick)} y="100" textAnchor="middle" fontSize="14">{tick}</text>
          </g>
        ))}
        {markers.map((marker) => (
          <g key={marker.label}>
            <circle cx={x(marker.value)} cy="70" r="5" fill="#8d4528" />
            <text x={x(marker.value)} y="48" textAnchor="middle" fontSize="14">{marker.label}</text>
          </g>
        ))}
        <circle cx={x(value)} cy="70" r="8" fill="#0e5c57" />
      </svg>
      <label>
        Posição: {value.toFixed(2)}
        <input type="range" min={min} max={max} step={config.step as number} value={value} onChange={(event) => setValue(Number(event.target.value))} />
      </label>
      <div className="controls">
        {markers.map((marker) => (
          <button key={marker.label} type="button" className="secondary" onClick={() => setValue(marker.value)}>{marker.label}</button>
        ))}
        <button type="button" className="secondary" onClick={() => setValue(config.initial as number)}>Restaurar</button>
      </div>
      <p className="live" aria-live="polite">Valor escolhido: {value.toFixed(2)}.</p>
    </figure>
  );
}

export function ArrayGrid({ config, description }: { config: Record<string, unknown>; description: string }) {
  const rowsAllowed = config.allowedRows as number[];
  const colsAllowed = config.allowedColumns as number[];
  const [rows, setRows] = useState(config.initialRows as number);
  const [columns, setColumns] = useState(config.initialColumns as number);
  const total = arrayTotal(rows, columns);
  const cells = useMemo(() => Array.from({ length: rows }, (_, row) => Array.from({ length: columns }, (_, column) => `${row}-${column}`)), [rows, columns]);
  return (
    <figure className="viz">
      <svg viewBox="0 0 640 360" role="img" aria-label={description}>
        {cells.flatMap((row, rowIndex) => row.map((key, columnIndex) => (
          <circle key={key} cx={80 + columnIndex * 48} cy={40 + rowIndex * 32} r="8" fill="#0e5c57" />
        )))}
      </svg>
      <div className="controls">
        <label>
          Fileiras
          <select value={rows} onChange={(event) => setRows(Number(event.target.value))}>
            {rowsAllowed.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <label>
          Em cada fileira
          <select value={columns} onChange={(event) => setColumns(Number(event.target.value))}>
            {colsAllowed.map((item) => <option key={item} value={item}>{item}</option>)}
          </select>
        </label>
        <button type="button" className="secondary" onClick={() => { setRows(config.initialRows as number); setColumns(config.initialColumns as number); }}>Restaurar</button>
      </div>
      <p className="live" aria-live="polite">{rows} fileiras de {columns} são {rows} × {columns} = {total}. Também é a soma {Array.from({ length: rows }, () => String(columns)).join(" + ")}.</p>
    </figure>
  );
}

export function BarCompare({ config, description }: { config: Record<string, unknown>; description: string }) {
  const bars = config.bars as Array<{ id: string; label: string; value: number }>;
  const [active, setActive] = useState(bars[0]?.id ?? "");
  const max = Math.max(...bars.map((bar) => bar.value), 1);
  const chosen = bars.find((bar) => bar.id === active);
  return (
    <figure className="viz">
      <svg viewBox="0 0 640 280" role="img" aria-label={description}>
        {bars.map((bar, index) => (
          <g key={bar.id} onClick={() => setActive(bar.id)}>
            <rect x={40 + index * 90} y={240 - (bar.value / max) * 180} width="60" height={(bar.value / max) * 180} fill={bar.id === active ? "#0e5c57" : "#8d4528"} />
            <text x={70 + index * 90} y="262" textAnchor="middle" fontSize="12">{bar.label}</text>
          </g>
        ))}
      </svg>
      <p>{String(config.question)}</p>
      <p className="live" aria-live="polite">{chosen ? `${chosen.label}: ${chosen.value} ${String(config.unit)}.` : ""}</p>
      <button type="button" className="secondary" onClick={() => setActive(bars[0]?.id ?? "")}>Restaurar</button>
    </figure>
  );
}
