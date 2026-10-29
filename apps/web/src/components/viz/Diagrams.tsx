"use client";

import { useState } from "react";

export function GeometryDiagram({ config, description }: { config: Record<string, unknown>; description: string }) {
  const [alternate, setAlternate] = useState(false);
  const polygons = (alternate && config.alternatePolygons ? config.alternatePolygons : config.polygons) as Array<{ points: Array<{ x: number; y: number }>; label: string; fill: string }>;
  return (
    <figure className="viz">
      <svg viewBox={`0 0 ${config.width} ${config.height}`} role="img" aria-label={description}>
        {polygons.map((polygon) => (
          <g key={polygon.label}>
            <polygon points={polygon.points.map((point) => `${point.x},${point.y}`).join(" ")} fill={polygon.fill} stroke="#1c2430" />
            <text x={polygon.points[0].x} y={polygon.points[0].y - 8} fontSize="16">{polygon.label}</text>
          </g>
        ))}
      </svg>
      <p>{String(config.caption)}</p>
      {config.toggleLabel ? (
        <button type="button" className="secondary" aria-pressed={alternate} onClick={() => setAlternate((value) => !value)}>
          {String(config.toggleLabel)}
        </button>
      ) : null}
    </figure>
  );
}

export function Comparison({ config, description }: { config: Record<string, unknown>; description: string }) {
  const [side, setSide] = useState<"both" | "left" | "right">("both");
  const rows = config.rows as Array<{ label: string; left: string; right: string }>;
  return (
    <figure className="viz">
      <p>{description}</p>
      <div className="controls" role="group" aria-label="Qual coluna destacar">
        <button type="button" className="secondary" aria-pressed={side === "both"} onClick={() => setSide("both")}>As duas</button>
        <button type="button" className="secondary" aria-pressed={side === "left"} onClick={() => setSide("left")}>{String(config.leftTitle)}</button>
        <button type="button" className="secondary" aria-pressed={side === "right"} onClick={() => setSide("right")}>{String(config.rightTitle)}</button>
      </div>
      <table>
        <caption className="live">{side === "both" ? "Comparando as duas colunas." : `Coluna em destaque: ${side === "left" ? config.leftTitle : config.rightTitle}.`}</caption>
        <thead>
          <tr>
            <th scope="col"> </th>
            <th scope="col">{String(config.leftTitle)}</th>
            <th scope="col">{String(config.rightTitle)}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.label}>
              <th scope="row">{row.label}</th>
              <td style={{ opacity: side === "right" ? 0.35 : 1 }}>{row.left}</td>
              <td style={{ opacity: side === "left" ? 0.35 : 1 }}>{row.right}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </figure>
  );
}

export function EventTimeline({ config, description }: { config: Record<string, unknown>; description: string }) {
  const events = config.events as Array<{ id: string; label: string; text: string }>;
  const [active, setActive] = useState(events[0]?.id ?? "");
  const chosen = events.find((event) => event.id === active);
  return (
    <figure className="viz">
      <p>{description}</p>
      <div className="controls" role="list">
        {events.map((event) => (
          <button key={event.id} type="button" className="secondary" aria-pressed={event.id === active} onClick={() => setActive(event.id)}>{event.label}</button>
        ))}
      </div>
      <p className="live" aria-live="polite">{chosen ? `${chosen.label}. ${chosen.text}` : ""}</p>
    </figure>
  );
}

export function StateSteps({ config, description }: { config: Record<string, unknown>; description: string }) {
  const steps = config.steps as Array<{ id: string; title: string; text: string }>;
  const [index, setIndex] = useState(0);
  const step = steps[index];
  return (
    <figure className="viz">
      <p>{description}</p>
      <ol className="stepper">
        {steps.map((item, itemIndex) => (
          <li key={item.id}>
            <button type="button" className="secondary" aria-current={itemIndex === index} onClick={() => setIndex(itemIndex)}>
              {itemIndex + 1}. {item.title}
            </button>
          </li>
        ))}
      </ol>
      <div className="controls">
        <button type="button" className="secondary" onClick={() => setIndex((value) => Math.max(0, value - 1))} disabled={index === 0}>Anterior</button>
        <button type="button" className="secondary" onClick={() => setIndex((value) => Math.min(steps.length - 1, value + 1))} disabled={index === steps.length - 1}>Próximo</button>
        <button type="button" className="secondary" onClick={() => setIndex(0)}>Restaurar</button>
      </div>
      <p className="live" aria-live="polite">Passo {index + 1} de {steps.length}. {step.title}. {step.text}</p>
    </figure>
  );
}

export function FieldRecord({ config, description }: { config: Record<string, unknown>; description: string }) {
  const fields = config.fields as Array<{ id: string; label: string; value: string }>;
  const [chosen, setChosen] = useState<string | null>(null);
  const correct = chosen === config.targetFieldId;
  return (
    <figure className="viz">
      <p>{description}</p>
      <p>{String(config.prompt)}</p>
      <div className="controls">
        {fields.map((field) => (
          <button key={field.id} type="button" className="secondary" aria-pressed={chosen === field.id} onClick={() => setChosen(field.id)}>
            <strong>{field.label}</strong>: {field.value}
          </button>
        ))}
        <button type="button" className="secondary" onClick={() => setChosen(null)}>Restaurar</button>
      </div>
      <p className="live" aria-live="polite">
        {chosen === null ? "Nenhum campo escolhido." : correct ? String(config.feedbackCorrect) : String(config.feedbackIncorrect)}
      </p>
    </figure>
  );
}
