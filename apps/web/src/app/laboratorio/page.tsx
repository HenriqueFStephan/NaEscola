"use client";

import { FunctionPlot } from "@/components/viz/Charts";

const sine = {
  family: "sine",
  parameters: {
    A: { label: "Amplitude A", min: 0.5, max: 3, step: 0.1, default: 1 },
    B: { label: "Frequência B", min: 0.5, max: 3, step: 0.1, default: 1 },
    C: { label: "Fase C", min: -3.14, max: 3.14, step: 0.1, default: 0 },
    D: { label: "Deslocamento D", min: -2, max: 2, step: 0.1, default: 0 },
  },
  xMin: -6.28,
  xMax: 6.28,
  samples: 240,
  xLabel: "x",
  yLabel: "y",
  yMin: -4,
  yMax: 4,
};

export default function LabPage() {
  return (
    <>
      <h1>Laboratório de gráficos</h1>
      <p>Esta tela não é uma aula dos anos 3 a 6. Trigonometria não faz parte desse recorte. O gráfico existe para uma aula futura configurar y = A · sen(Bx + C) + D sem reescrever o componente.</p>
      <FunctionPlot config={sine} description="Gráfico de y igual a A vezes seno de Bx mais C, mais D. Os controles mudam A, B, C e D." />
    </>
  );
}
