import { geoNaturalEarth1, geoPath } from "d3-geo";
import { useMemo } from "react";
import { feature } from "topojson-client";
import type { GeometryCollection, Topology } from "topojson-specification";
import land110 from "world-atlas/land-110m.json";
import { formatCount, formatSigned, titleCase } from "../../data/format";
import "./flowmap.css";

export interface Flow { market: string; at: [number, number]; region?: boolean; base: number; sim: number }

const WIDTH = 960, HEIGHT = 500;
const projection = geoNaturalEarth1().center([40, 22]).scale(250).translate([WIDTH / 2, HEIGHT / 2]);
const path = geoPath(projection);
const topology = land110 as unknown as Topology<{ land: GeometryCollection }>;
const LAND = path(feature(topology, topology.objects.land)) ?? "";

/** Source markets to Abu Dhabi: arc width and dot size grow with weekly guests; the selected
 *  market's arc shows today (thin) and with the changes (thick). Click a market to select it. */
export function FlowMap({ flows, hub, domestic, selected, onSelect }: {
  flows: Flow[]; hub: [number, number]; domestic: { base: number; sim: number } | null; selected: string; onSelect: (market: string) => void;
}) {
  const [hx, hy] = projection(hub)!;
  const max = useMemo(() => Math.max(...flows.map((f) => Math.max(f.base, f.sim)), domestic?.base ?? 0), [flows, domestic]);
  const width = (v: number) => 1 + 13 * Math.sqrt(v / max);
  const ordered = [...flows].sort((a, b) => (a.market === selected ? 1 : b.market === selected ? -1 : b.base - a.base));
  return (
    <svg className="flowmap" viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-label="Weekly hotel guests by source market, flowing to Abu Dhabi">
      <path className="flowmap__land" d={LAND} />
      {ordered.map((f) => {
        const [x, y] = projection(f.at)!;
        const lift = Math.min(160, Math.hypot(x - hx, y - hy) * 0.35);
        const d = `M${x},${y} Q${(x + hx) / 2},${(y + hy) / 2 - lift} ${hx},${hy}`;
        const isSelected = f.market === selected;
        const delta = f.sim - f.base;
        return (
          <g key={f.market} className={`flowmap__flow${isSelected ? " flowmap__flow--selected" : ""}`} onClick={() => onSelect(f.market)}
             role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect(f.market); }}
             aria-label={`${titleCase(f.market)}: ${formatCount(f.sim)} guests a week`}>
            <title>{`${titleCase(f.market)}: ${formatCount(f.base)} guests a week today${isSelected && delta ? `, ${formatSigned(delta, formatCount)} with your changes` : ""}`}</title>
            <path className="flowmap__arc" d={d} style={{ strokeWidth: width(isSelected ? f.sim : f.base) }} />
            {isSelected && delta !== 0 && <path className="flowmap__arc flowmap__arc--today" d={d} style={{ strokeWidth: width(f.base) }} />}
            <circle className={f.region ? "flowmap__dot flowmap__dot--region" : "flowmap__dot"} cx={x} cy={y} r={2 + width(f.base) / 2} />
            {(isSelected || f.base / max > 0.25) && (
              <text className="flowmap__label" x={x} y={y - 8 - width(f.base) / 2}>
                {titleCase(f.market.replace(/^OTHER_/, ""))}{isSelected && delta !== 0 ? ` ${formatSigned(delta, formatCount)}` : ""}
              </text>
            )}
          </g>
        );
      })}
      {domestic && <circle className="flowmap__hub-ring" cx={hx} cy={hy} r={4 + width(domestic.base) / 1.5} />}
      <circle className="flowmap__hub" cx={hx} cy={hy} r={6} />
      <text className="flowmap__label flowmap__label--hub" x={hx + 10} y={hy + 18}>Abu Dhabi</text>
    </svg>
  );
}
