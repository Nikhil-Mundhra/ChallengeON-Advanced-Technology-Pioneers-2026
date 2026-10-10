/** Map projection, land outline and market-to-hub arcs, shared by FlowMap (SVG) and FlowDots (canvas). */
import { geoNaturalEarth1, geoPath } from "d3-geo";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import land110 from "world-atlas/land-110m.json";

export const MAP_WIDTH = 960, MAP_HEIGHT = 500;
export const projection = geoNaturalEarth1().center([40, 22]).scale(250).translate([MAP_WIDTH / 2, MAP_HEIGHT / 2]);
const topology = land110 as unknown as Topology<{ land: GeometryCollection }>;
export const LAND = geoPath(projection)(feature(topology, topology.objects.land)) ?? "";

export interface Arc { from: [number, number]; control: [number, number]; to: [number, number] }

/** The curve from a market to the hub, in map coordinates. */
export function arcBetween(at: [number, number], hub: [number, number]): Arc {
  const [x, y] = projection(at)!, [hx, hy] = projection(hub)!;
  const lift = Math.min(160, Math.hypot(x - hx, y - hy) * 0.35);
  return { from: [x, y], control: [(x + hx) / 2, (y + hy) / 2 - lift], to: [hx, hy] };
}

/** Point at t (0..1) along an arc. */
export function pointOn({ from, control, to }: Arc, t: number): [number, number] {
  const u = 1 - t;
  return [u * u * from[0] + 2 * u * t * control[0] + t * t * to[0], u * u * from[1] + 2 * u * t * control[1] + t * t * to[1]];
}

/** Velocity vector [dx, dy] at t (0..1) along an arc. */
export function tangentOn({ from, control, to }: Arc, t: number): [number, number] {
  const u = 1 - t;
  return [
    2 * u * (control[0] - from[0]) + 2 * t * (to[0] - control[0]),
    2 * u * (control[1] - from[1]) + 2 * t * (to[1] - control[1]),
  ];
}
