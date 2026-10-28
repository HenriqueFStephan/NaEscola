import { describe, expect, it } from "vitest";
import { arrayTotal, evaluate } from "./functions";

describe("allowlisted functions", () => {
  it("matches the sine, linear, and quadratic definitions", () => {
    expect(evaluate("sine", { A: 2, B: 1, C: 0, D: 0 }, Math.PI / 2)).toBeCloseTo(2);
    expect(evaluate("sine", { A: 1, B: 1, C: 0, D: 3 }, 0)).toBeCloseTo(3);
    expect(evaluate("linear", { A: 2, B: -1 }, 4)).toBe(7);
    expect(evaluate("quadratic", { A: 1, B: 0, C: -1 }, 3)).toBe(8);
  });

  it("counts a rectangular array", () => {
    expect(arrayTotal(3, 4)).toBe(12);
    expect(arrayTotal(10, 10)).toBe(100);
  });
});
