import { useEffect, useRef } from "react";
import { MAP_HEIGHT, MAP_WIDTH, pointOn, type Arc } from "./mapGeometry";

export type DotMode = "in" | "out" | "both";
interface Dot { arc: Arc; t: number; out: boolean; speed: number }

const TRAVEL_SECONDS = 1.8;
const MAX_DOTS = 1600;
/** Moving dots along the arcs, drawn on a canvas over the map: arriving dots travel to Abu Dhabi,
 *  leaving dots travel back. Each market sends one dot per `perDot` people per week, per second.
 *  Nothing moves when the reader prefers reduced motion or the tab is hidden. */
export function FlowDots({ arcs, rates, mode, perDot, playing }: {
  arcs: Record<string, Arc>; rates: Record<string, { in: number; out: number }>; mode: DotMode; perDot: number; playing: boolean;
}) {
  const canvas = useRef<HTMLCanvasElement>(null);
  const live = useRef({ rates, mode, perDot, playing, arcs });
  live.current = { rates, mode, perDot, playing, arcs };

  useEffect(() => {
    const node = canvas.current;
    if (!node || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const ctx = node.getContext("2d")!;
    const styles = getComputedStyle(node);
    const colourIn = styles.getPropertyValue("--color-accent").trim() || "#00605f";
    const colourOut = styles.getPropertyValue("--color-series-check").trim() || "#f77860";
    const dots: Dot[] = [];
    const owed: Record<string, { in: number; out: number }> = {};
    let last = performance.now(), frame = 0;

    const resize = () => {
      const ratio = window.devicePixelRatio || 1;
      node.width = node.clientWidth * ratio; node.height = node.clientHeight * ratio;
      ctx.setTransform((node.width / MAP_WIDTH), 0, 0, (node.height / MAP_HEIGHT), 0, 0);
    };
    const observer = new ResizeObserver(resize);
    observer.observe(node); resize();

    const tick = (now: number) => {
      const dt = Math.min(0.1, (now - last) / 1000); last = now;
      const { rates: r, mode: m, perDot: unit, playing: on, arcs: a } = live.current;
      if (on && unit > 0) {
        for (const [market, rate] of Object.entries(r)) {
          const arc = a[market]; if (!arc) continue;
          const o = (owed[market] ??= { in: 0, out: 0 });
          if (m !== "out") o.in += (rate.in / unit) * dt;
          if (m !== "in") o.out += (rate.out / unit) * dt;
          while (o.in >= 1 && dots.length < MAX_DOTS) { o.in -= 1; dots.push({ arc, t: 0, out: false, speed: (0.85 + Math.random() * 0.3) / TRAVEL_SECONDS }); }
          while (o.out >= 1 && dots.length < MAX_DOTS) { o.out -= 1; dots.push({ arc, t: 0, out: true, speed: (0.85 + Math.random() * 0.3) / TRAVEL_SECONDS }); }
          o.in = Math.min(o.in, 1); o.out = Math.min(o.out, 1);
        }
      }
      ctx.clearRect(0, 0, MAP_WIDTH, MAP_HEIGHT);
      for (let i = dots.length - 1; i >= 0; i -= 1) {
        const d = dots[i];
        d.t += d.speed * dt;
        if (d.t >= 1 || (d.out ? m === "in" : m === "out")) { dots.splice(i, 1); continue; }
        const [x, y] = pointOn(d.arc, d.out ? 1 - d.t : d.t);
        ctx.globalAlpha = Math.sin(Math.PI * d.t) * 0.75 + 0.25;
        ctx.fillStyle = d.out ? colourOut : colourIn;
        ctx.beginPath(); ctx.arc(x, y, 2.4, 0, Math.PI * 2); ctx.fill();
      }
      ctx.globalAlpha = 1;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => { cancelAnimationFrame(frame); observer.disconnect(); };
  }, []);

  return <canvas ref={canvas} className="flowmap__dots" aria-hidden="true" />;
}
