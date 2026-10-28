import { describe, expect, it } from "vitest";
import { project } from "./project";

const view = { minLon: -12, minLat: 24, maxLon: 48, maxLat: 54 };

describe("equirectangular window", () => {
  it("maps the view corners to the svg frame", () => {
    expect(project(-12, 54, view, 800, 400)).toEqual([0, 0]);
    expect(project(48, 24, view, 800, 400)).toEqual([800, 400]);
  });
});
