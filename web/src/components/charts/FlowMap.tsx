import { marketName } from "../../content/labels";
import { useCallback, useMemo, useRef, useState } from "react";
import { formatCount, formatSigned } from "../../data/format";
import { FlowDots, type DotMode } from "./FlowDots";
import { arcBetween, GRATICULES, LAND, MAP_HEIGHT, MAP_WIDTH, projection } from "./mapGeometry";
import "./flowmap.css";

export interface Flow { market: string; at: [number, number]; region?: boolean; base: number; sim: number; checkIns?: number; checkOuts?: number }
export type { DotMode };

const MIN_ZOOM = 1;
const MAX_ZOOM = 5;

function clampPan(px: number, py: number, z: number) {
  const limitX = (MAP_WIDTH * (z - 1)) / 2 + MAP_WIDTH * 0.45;
  const limitY = (MAP_HEIGHT * (z - 1)) / 2 + MAP_HEIGHT * 0.4;
  const centerX = (1 - z) * (MAP_WIDTH / 2);
  const centerY = (1 - z) * (MAP_HEIGHT / 2);
  return {
    x: Math.min(centerX + limitX, Math.max(centerX - limitX, px)),
    y: Math.min(centerY + limitY, Math.max(centerY - limitY, py)),
  };
}

/** Source markets to Abu Dhabi: arc width and dot size grow with weekly guests; the selected
 *  market's arc shows today (dashed) and with the changes. Optional moving dots show people
 *  arriving and leaving. Click a market to select it. Supports pan and zoom. */
export function FlowMap({ flows, hub, domestic, selected, onSelect, dots, highlight }: {
  flows: Flow[]; hub: [number, number]; domestic: { base: number; sim: number } | null; selected: string; onSelect: (market: string) => void;
  dots?: { mode: DotMode; perDot: number; playing: boolean };
  highlight?: ReadonlySet<string>;   // markets with an event this week
}) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const dragStart = useRef<{ x: number; y: number; panX: number; panY: number } | null>(null);
  const dragMoved = useRef(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const applyZoom = useCallback((targetZoom: number, center: [number, number] = [MAP_WIDTH / 2, MAP_HEIGHT / 2]) => {
    const z = Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, Math.round(targetZoom * 100) / 100));
    setZoom((prevZoom) => {
      if (z === prevZoom) return prevZoom;
      setPan((prevPan) => {
        const [cx, cy] = center;
        const newPanX = prevPan.x + (prevZoom - z) * cx;
        const newPanY = prevPan.y + (prevZoom - z) * cy;
        return clampPan(newPanX, newPanY, z);
      });
      return z;
    });
  }, []);

  const zoomIn = () => applyZoom(zoom * 1.35);
  const zoomOut = () => applyZoom(zoom / 1.35);
  const reset = () => { setZoom(1); setPan({ x: 0, y: 0 }); };

  const handleWheel = (e: React.WheelEvent<HTMLDivElement>) => {
    e.preventDefault();
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const mx = (e.clientX - rect.left) * (MAP_WIDTH / rect.width);
    const my = (e.clientY - rect.top) * (MAP_HEIGHT / rect.height);
    const cx = (mx - pan.x) / zoom;
    const cy = (my - pan.y) / zoom;
    const factor = e.deltaY < 0 ? 1.15 : 1 / 1.15;
    applyZoom(zoom * factor, [cx, cy]);
  };

  const handlePointerDown = (e: React.PointerEvent<HTMLDivElement>) => {
    if (e.button !== 0 && e.pointerType === "mouse") return;
    dragStart.current = { x: e.clientX, y: e.clientY, panX: pan.x, panY: pan.y };
    dragMoved.current = false;
    setIsDragging(true);
  };

  const handlePointerMove = (e: React.PointerEvent<HTMLDivElement>) => {
    if (!dragStart.current) return;
    const rect = containerRef.current?.getBoundingClientRect();
    if (!rect) return;
    const dx = (e.clientX - dragStart.current.x) * (MAP_WIDTH / rect.width);
    const dy = (e.clientY - dragStart.current.y) * (MAP_HEIGHT / rect.height);
    if (Math.hypot(dx, dy) > 4) {
      dragMoved.current = true;
    }
    setPan(clampPan(dragStart.current.panX + dx, dragStart.current.panY + dy, zoom));
  };

  const handlePointerUp = () => {
    dragStart.current = null;
    setIsDragging(false);
  };

  const [hx, hy] = projection(hub)!;
  const max = useMemo(() => Math.max(...flows.map((f) => Math.max(f.base, f.sim)), domestic?.base ?? 0), [flows, domestic]);
  const width = (v: number) => 1 + 13 * Math.sqrt(Math.max(v, 0) / max);
  const ordered = [...flows].sort((a, b) => (a.market === selected ? 1 : b.market === selected ? -1 : b.base - a.base));
  const arcs = useMemo(() => Object.fromEntries(flows.map((f) => [f.market, arcBetween(f.at, hub)])), [flows, hub]);
  return (
    <div
      ref={containerRef}
      className={`flowmap flowmap--draggable${isDragging ? " flowmap--dragging" : ""}`}
      onWheel={handleWheel}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
    >
      <div className="flowmap__controls" role="toolbar" aria-label="Map zoom controls">
        <button type="button" className="flowmap__control-btn" onClick={zoomIn} disabled={zoom >= MAX_ZOOM} aria-label="Zoom in" title="Zoom in">+</button>
        <button type="button" className="flowmap__control-btn" onClick={zoomOut} disabled={zoom <= MIN_ZOOM} aria-label="Zoom out" title="Zoom out">−</button>
        <button type="button" className="flowmap__control-btn flowmap__control-btn--reset" onClick={reset} disabled={zoom === 1 && pan.x === 0 && pan.y === 0} aria-label="Reset zoom and position" title="Fit map">Fit</button>
      </div>
      <svg className="flowmap__svg" viewBox={`0 0 ${MAP_WIDTH} ${MAP_HEIGHT}`} role="img" aria-label="Hotel nights by where visitors fly from, flowing to Abu Dhabi">
        <g transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}>
          <path className="flowmap__graticule" d={GRATICULES} />
          <path className="flowmap__land" d={LAND} />
          {ordered.map((f) => {
            const { from: [x, y], control: [cx, cy] } = arcs[f.market];
            const d = `M${x},${y} Q${cx},${cy} ${hx},${hy}`;
            const isSelected = f.market === selected;
            const delta = f.sim - f.base;
            return (
              <g key={f.market} className={`flowmap__flow${isSelected ? " flowmap__flow--selected" : ""}${highlight?.has(f.market) ? " flowmap__flow--event" : ""}`}
                 onClick={() => { if (!dragMoved.current) onSelect(f.market); }}
                 role="button" tabIndex={0} onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect(f.market); }}
                 aria-label={`${marketName(f.market)}: ${formatCount(f.sim)} hotel nights a week`}>
                <title>{`${marketName(f.market)}: ${formatCount(f.sim)} hotel nights a week${isSelected && delta ? ` (${formatSigned(delta, formatCount)} from your changes)` : ""}`}</title>
                <path className="flowmap__arc" d={d} style={{ strokeWidth: width(isSelected ? f.sim : f.base) }} />
                {isSelected && Math.abs(delta) >= 1 && <path className="flowmap__arc flowmap__arc--today" d={d} style={{ strokeWidth: width(f.base) }} />}
                <circle className={f.region ? "flowmap__dot flowmap__dot--region" : "flowmap__dot"} cx={x} cy={y} r={2 + width(f.sim) / 2} />
                {(isSelected || f.base / max > 0.25) && (
                  <text className="flowmap__label" x={x} y={y - 8 - width(f.sim) / 2}>
                    {marketName(f.market).replace(/^Other /, "")}{isSelected && Math.abs(delta) >= 1 ? ` ${formatSigned(delta, formatCount)}` : ""}
                  </text>
                )}
              </g>
            );
          })}
          {domestic && (
            <g className={`flowmap__flow flowmap__hub-group${selected === "DOMESTIC" ? " flowmap__flow--selected" : ""}`}
               onClick={() => { if (!dragMoved.current) onSelect("DOMESTIC"); }} role="button" tabIndex={0}
               onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") onSelect("DOMESTIC"); }}
               aria-label={`Abu Dhabi (Domestic): ${formatCount(domestic.sim)} hotel nights a week`}>
              <title>{`Abu Dhabi (Domestic): ${formatCount(domestic.sim)} hotel nights a week${selected === "DOMESTIC" && Math.abs(domestic.sim - domestic.base) >= 1 ? ` (${formatSigned(domestic.sim - domestic.base, formatCount)} from your changes)` : ""}`}</title>
              <circle className="flowmap__hub-ring" cx={hx} cy={hy} r={4 + width(domestic.sim) / 1.5} />
              <circle className="flowmap__hub" cx={hx} cy={hy} r={6} />
              <text className="flowmap__label flowmap__label--hub" x={hx + 10} y={hy + 18}>
                Abu Dhabi{selected === "DOMESTIC" && Math.abs(domestic.sim - domestic.base) >= 1 ? ` ${formatSigned(domestic.sim - domestic.base, formatCount)}` : ""}
              </text>
            </g>
          )}
          {!domestic && (
            <>
              <circle className="flowmap__hub" cx={hx} cy={hy} r={6} />
              <text className="flowmap__label flowmap__label--hub" x={hx + 10} y={hy + 18}>Abu Dhabi</text>
            </>
          )}
        </g>
      </svg>
      {dots && (
        <FlowDots arcs={arcs} mode={dots.mode} perDot={dots.perDot} playing={dots.playing}
                  rates={Object.fromEntries(flows.map((f) => [f.market, { in: f.checkIns ?? 0, out: f.checkOuts ?? 0 }]))}
                  zoom={zoom} pan={pan} />
      )}
    </div>
  );
}
