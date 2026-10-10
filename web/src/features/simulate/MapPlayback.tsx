import { useEffect, useMemo, useRef, useState } from "react";
import { Area, AreaChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis } from "recharts";
import { FlowMap, type DotMode } from "../../components/charts/FlowMap";
import { SERIES } from "../../components/charts/theme";
import { Badge, Segmented } from "../../components/ui";
import { ABU_DHABI, MARKET_POSITIONS } from "../../content/geo";
import { eventName, marketName } from "../../content/labels";
import { formatCount, formatDate, formatMonth, formatPercent, formatSigned, toneOf } from "../../data/format";
import { frameAt, type Playback } from "../../engine/playback";

const MODES = [{ value: "both", label: "Both" }, { value: "in", label: "Arriving" }, { value: "out", label: "Leaving" }] as const;
const SPEEDS = [{ value: "1", label: "1×" }, { value: "4", label: "4×" }] as const;
const WEEK_MS = 700;

/** The moving map: press play and the weeks run from the past into the forecast; dots show people
 *  arriving and leaving, the counters below say what that week means. The week shown is owned by
 *  the page (`week`, `onWeek`) so other panels follow it. */
export function MapPlayback({ pb, selected, week: w, onWeek: setW, onSelect }: {
  pb: Playback; selected: string; week: number; onWeek: (week: number) => void; onSelect: (m: string) => void;
}) {
  const current = useRef(w);
  current.current = w;
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<"1" | "4">("1");
  const [mode, setMode] = useState<DotMode>("both");
  const last = pb.weeks.length - 1;

  useEffect(() => {
    if (!playing) return;
    const id = setInterval(() => setW(Math.min(current.current + 1, last)), WEEK_MS / Number(speed));
    return () => clearInterval(id);
  }, [playing, speed, last, setW]);
  useEffect(() => { if (w >= last) setPlaying(false); }, [w, last]);

  const perDot = useMemo(() => {
    const arrivals = pb.weeks.map((_, i) => Object.entries(pb.markets).reduce((s, [m, v]) => (m === "DOMESTIC" ? s : s + v.checkIns[i]), 0));
    return Math.max(1, Math.round(arrivals.reduce((a, b) => a + b, 0) / arrivals.length / 60 / 10) * 10);
  }, [pb]);

  const safeW = Math.min(Math.max(0, w), last);
  const frame = frameAt(pb, safeW, selected);
  const flows = Object.entries(pb.markets).filter(([m]) => MARKET_POSITIONS[m]).map(([market, s]) => ({
    market, ...MARKET_POSITIONS[market], base: s.guests[safeW] - s.extra[safeW], sim: s.guests[safeW], checkIns: s.checkIns[safeW], checkOuts: s.checkOuts[safeW],
  }));
  const home = pb.markets.DOMESTIC;
  const eventMarkets = new Set(frame.events.flatMap((e) => e.markets));
  const series = useMemo(() => pb.weeks.map((week, i) => ({ week, total: pb.total[i] })), [pb]);
  const lastReal = pb.weeks[Math.max(0, pb.kind.lastIndexOf("history"))];

  return (
    <div className="playback">
      <div className="playback__bar">
        <button type="button" className="pill pill--dark" onClick={() => { if (w >= last) setW(0); setPlaying(!playing); }} aria-pressed={playing}>
          {playing ? "Pause" : "Play"}
        </button>
        <Segmented label="Speed" value={speed} onChange={setSpeed} options={SPEEDS} />
        <Segmented label="Show people" value={mode} onChange={setMode} options={MODES} />
        <span className="playback__legend"><i className="playback__swatch playback__swatch--in" />arriving <i className="playback__swatch playback__swatch--out" />leaving · 1 plane ≈ {formatCount(perDot)} people a week</span>
      </div>

      <FlowMap flows={flows} hub={ABU_DHABI} domestic={home ? { base: home.guests[safeW] - home.extra[safeW], sim: home.guests[safeW] } : null}
               selected={selected} onSelect={onSelect} dots={{ mode, perDot, playing }} highlight={eventMarkets} />
      <p className="playback__event" aria-live="polite">
        {frame.events.length ? `★ This week: ${frame.events.map((e) => eventName(e.code)).join(", ")}` : "\u00a0"}
      </p>

      <div className="playback__scrub">
        <ResponsiveContainer width="100%" height={56}>
          <AreaChart data={series} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}
                     onClick={(e) => {
                       const idx = e?.activeTooltipIndex !== undefined
                         ? Number(e.activeTooltipIndex)
                         : pb.weeks.indexOf(String(e?.activeLabel ?? ""));
                       if (idx >= 0 && idx <= last) { setW(idx); setPlaying(false); }
                     }}>
            <XAxis dataKey="week" hide />
            <Tooltip content={() => null} cursor={false} />
            <Area dataKey="total" stroke={SERIES.actual} fill={SERIES.scenario} fillOpacity={0.15} isAnimationActive={false} dot={false} />
            <ReferenceLine x={lastReal} stroke="var(--color-text-muted)" strokeDasharray="3 3" />
            <ReferenceLine x={pb.weeks[w]} stroke={SERIES.check} strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
        <input type="range" min={0} max={last} value={w} onChange={(e) => { setW(Number(e.target.value)); setPlaying(false); }}
               aria-label="Week" className="playback__range" />
        <div className="playback__ends"><span>{formatMonth(pb.weeks[0])}</span><span>real data to {formatMonth(lastReal)}, forecast after</span><span>{formatMonth(pb.weeks[last])}</span></div>
      </div>

      <dl className="playback__facts" aria-live="polite">
        <div><dt>Week of</dt><dd>{formatDate(frame.week)} <Badge tone="neutral">{frame.kind === "history" ? "real" : "forecast"}</Badge></dd></div>
        <div><dt>Hotel nights this week</dt><dd>{formatCount(frame.total)}</dd></div>
        <div><dt>Compared with a year before</dt><dd className={frame.vsLastYear === null ? undefined : toneOf(frame.vsLastYear)}>{frame.vsLastYear === null ? "n/a" : formatPercent(frame.vsLastYear)}</dd></div>
        <div><dt>Arriving most this week</dt><dd className="playback__top">
          {frame.topArrivals.map((t) => <span key={t.market}><span>{marketName(t.market)}</span><span>{formatCount(t.checkIns)}</span></span>)}
        </dd></div>
        <div><dt>Your changes so far</dt>{selected === "ALL"
          ? <dd className="playback__muted">pick a market</dd>
          : <dd className={toneOf(frame.extraSoFar)}>{formatSigned(frame.extraSoFar, formatCount)} nights</dd>}</div>
      </dl>
    </div>
  );
}
