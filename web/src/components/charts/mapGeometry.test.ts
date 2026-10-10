import { describe, expect, it } from "vitest";
import { pointOn, tangentOn, type Arc } from "./mapGeometry";

describe("mapGeometry", () => {
  const horizontalArc: Arc = {
    from: [0, 100],
    control: [50, 50],
    to: [100, 100],
  };

  it("pointOn evaluates bezier endpoints and midpoint accurately", () => {
    expect(pointOn(horizontalArc, 0)).toEqual([0, 100]);
    expect(pointOn(horizontalArc, 1)).toEqual([100, 100]);
    // Midpoint: 0.25*100 + 0.5*50 + 0.25*100 = 75 for y, 50 for x
    expect(pointOn(horizontalArc, 0.5)).toEqual([50, 75]);
  });

  it("tangentOn computes velocity vectors matching trajectory direction", () => {
    // At t=0: derivative is 2*(control - from) = 2*([50, -50]) = [100, -100]
    const [dx0, dy0] = tangentOn(horizontalArc, 0);
    expect(dx0).toBeCloseTo(100);
    expect(dy0).toBeCloseTo(-100);

    // At t=0.5: derivative is 2*0.5*([50,-50]) + 2*0.5*([50,50]) = [100, 0]
    const [dxMid, dyMid] = tangentOn(horizontalArc, 0.5);
    expect(dxMid).toBeCloseTo(100);
    expect(dyMid).toBeCloseTo(0);

    // At t=1: derivative is 2*(to - control) = 2*([50, 50]) = [100, 100]
    const [dx1, dy1] = tangentOn(horizontalArc, 1);
    expect(dx1).toBeCloseTo(100);
    expect(dy1).toBeCloseTo(100);
  });

  it("reverse travel direction is opposite (180 degrees) of forward travel", () => {
    // At midpoint: forward heading is atan2(0, 100) = 0
    const [dxFwd, dyFwd] = tangentOn(horizontalArc, 0.5);
    const angleFwd = Math.atan2(dyFwd, dxFwd);
    expect(angleFwd).toBeCloseTo(0);

    // Reverse heading with negated velocity: atan2(-0, -100) = Math.PI (180 degrees)
    const angleRev = Math.atan2(-dyFwd, -dxFwd);
    expect(Math.abs(angleRev)).toBeCloseTo(Math.PI);
  });
});
