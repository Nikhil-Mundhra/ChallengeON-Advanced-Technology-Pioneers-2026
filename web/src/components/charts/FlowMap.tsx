import { useMemo } from "react";
import { formatCount, formatSigned, titleCase } from "../../data/format";
import { FlowDots, type DotMode } from "./FlowDots";
import { arcBetween, LAND, MAP_HEIGHT, MAP_WIDTH, projection } from "./mapGeometry";
import "./flowmap.css";

export interface Flow { market: string; at: [number, number]; region?: boolean; base: number; sim: number; checkIns?: number; checkOuts?: number }
export type { DotMode };

/** Source markets to Abu Dhabi: arc width and dot size grow with weekly guests; the selected
 *  market's arc shows today (dashed) and with the changes. Optional moving dots show people
 *  arriving and leaving. Click a market to select it. */
export function FlowMap({ flows, hub, domestic, selected, onSelect, dots, highlight }: {
  flows: Flow[]; hub: [number, number]; domestic: { base: number; sim: number } | null; selected: string; onSelect: (market: string) => void;
  dots?: { mode: DotMode; perDot: number; playing: boolean };
  highlight?: ReadonlySet<string>;   // markets with an event this week
}) {
  const [hx, hy] = projection(hub)!;
  const max = useMemo(() => Math.max(...flows.map((f) => Math.max(f.base, f.sim)), domestic?.base ?? 0), [flows, domestic]);
  const width = (v: number) => 1 + 13 * Math.sqrt(Math.max(v, 0) / max);
  const ordered = [...flows].sort((a, b) => (a.market === selected ? 1 : b.market === selected ? -1 : b.base - a.base));
  const arcs = useMemo(() => Object.fromEntries(flows.map((f) => [f.market, arcBetween(f.at, hub)])), [flows, hub]);
  return (
    <div className="flowmap">
      <svg className="flowmap__svg" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} role="img" aria-label="Hotel guests by where visitors fly from, flowing to Abu Dhabi">
        <path className="flowmap__land" d={LAND} />
        {ordered.map((f) => {
          const { from: [x, y], control: [cx, cy] } = arcs[f.market];
          const d = `M${x},${y} Q${cx},${cy} ${hx},${hy}`;
          const isSelected = f.market === selected;
          const delta = f.sim - f.base;
          return (
            <g key={f.market} className={`flowmap__flow${isSelected ? " flowmap__flow--selected" : ""}${highlight?.has(f.market) ? " flowmap__flow--event" : ""}`} onClick={() => onSelect(f.market)}
               role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect(f.market); }}
               aria-label={`${titleCase(f.market)}: ${formatCount(f.sim)} guests a week`}>
              <title>{`${titleCase(f.market)}: ${formatCount(f.sim)} guests a week${isSelected && delta ? ` (${formatSigned(delta, formatCount)} from your changes)` : ""}`}</title>
              <path className="flowmap__arc" d={d} style={{ strokeWidth: width(isSelected ? f.sim : f.base) }} />
              {isSelected && Math.abs(delta) >= 1 && <path className="flowmap__arc flowmap__arc--today" d={d} style={{ strokeWidth: width(f.base) }} />}
              <circle className={f.region ? "flowmap__dot flowmap__dot--region" : "flowmap__dot"} cx={x} cy={y} r={2 + width(f.sim) / 2} />
              {(isSelected || f.base / max > 0.25) && (
                <text className="flowmap__label" x={x} y={y - 8 - width(f.sim) / 2}>
                  {titleCase(f.market.replace(/^OTHER_/, ""))}{isSelected && Math.abs(delta) >= 1 ? ` ${formatSigned(delta, formatCount)}` : ""}
                </text>
              )}
            </g>
          );
        })}
        {domestic && <circle className="flowmap__hub-ring" cx={hx} cy={hy} r={4 + width(domestic.sim) / 1.5} />}
        <circle className="flowmap__hub" cx={hx} cy={hy} r={6} />
        <text className="flowmap__label flowmap__label--hub" x={hx + 10} y={hy + 18}>Abu Dhabi</text>
      </svg>
      {dots && (
        <FlowDots arcs={arcs} mode={dots.mode} perDot={dots.perDot} playing={dots.playing}
                  rates={Object.fromEntries(flows.map((f) => [f.market, { in: f.checkIns ?? 0, out: f.checkOuts ?? 0 }]))} />
      )}
    </div>
  );
}
