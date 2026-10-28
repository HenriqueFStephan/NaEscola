export type FunctionFamily = "sine" | "linear" | "quadratic";

export function evaluate(family: FunctionFamily, parameters: Record<string, number>, x: number): number {
  if (family === "sine") {
    return parameters.A * Math.sin(parameters.B * x + parameters.C) + parameters.D;
  }
  if (family === "linear") {
    return parameters.A * x + parameters.B;
  }
  return parameters.A * x * x + parameters.B * x + parameters.C;
}

export function samples(
  family: FunctionFamily,
  parameters: Record<string, number>,
  xMin: number,
  xMax: number,
  count: number,
): Array<{ x: number; y: number }> {
  if (count < 2 || xMin >= xMax) {
    throw new Error("Invalid sample domain.");
  }
  const step = (xMax - xMin) / (count - 1);
  return Array.from({ length: count }, (_, index) => {
    const x = xMin + index * step;
    return { x, y: evaluate(family, parameters, x) };
  });
}

export function arrayTotal(rows: number, columns: number): number {
  return rows * columns;
}
