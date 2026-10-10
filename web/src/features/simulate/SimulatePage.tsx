import { useMemo, useReducer, useState } from "react";
import { Tornado } from "../../components/charts/Tornado";
import { Waterfall } from "../../components/charts/Waterfall";
import { Badge, Card, Chips, ControlSection, Segmented, Select, SliderRow, StatCard } from "../../components/ui";
import { leverName, SEASON_MONTHS, SEASON_NAMES } from "../../content/labels";
import { formatFull, formatMonth, formatPercent, formatSigned, titleCase, toneOf } from "../../data/format";
import { tornado, weeklyHeadline, type Planning, type SimulationResult, type WeeklyHeadline } from "../../engine/planning";
import { playback } from "../../engine/playback";
import { holdoutWmape, timeline, yearTotals, type Weekly } from "../../engine/weekly";
import { activePreset, DEFAULT_INPUT, groupChanged, LEVER_GROUPS, leverReducer, marketOptions, PRESETS, toLever } from "./levers";
import { MapPlayback } from "./MapPlayback";
import { TimelinePanel } from "./TimelinePanel";
import "./simulate.css";

const VIEWS = [
  { value: "map", label: "Map" }, { value: "time", label: "Over time" }, { value: "chain", label: "How it adds up" }, { value: "levers", label: "Biggest levers" },
] as const;
type View = (typeof VIEWS)[number]["value"];

/** Flight scenario workbench: levers on the left, one visual at a time in the centre, results on
 *  the right. Numbers come from engine/planning.ts and engine/weekly.ts; this file words and lays them out. */
export function SimulatePage({ planning, weekly }: { planning: Planning; weekly: Weekly }) {
  const markets = useMemo(() => marketOptions(planning), [planning]);
  const seasons = useMemo(() => Object.keys(Object.values(planning.calibration)[0]), [planning]);
  const [market, setMarket] = useState("UNITED KINGDOM");
  const [season, setSeason] = useState(seasons[0]);
  const [input, dispatch] = useReducer(leverReducer, DEFAULT_INPUT);
  const [view, setView] = useState<View>("map");
  const [start, setStart] = useState(weekly.last_actual_week);
  const [growthPct, setGrowthPct] = useState(0);

  const lever = useMemo(() => toLever(input), [input]);
  const headline = weeklyHeadline(planning, market, season, lever);
  const pb = useMemo(() => playback(planning, weekly, market, lever, { start, growthPct }), [planning, weekly, market, lever, start, growthPct]);
  const points = useMemo(() => timeline(planning, weekly, market, lever, { start, growthPct }), [planning, weekly, market, lever, start, growthPct]);
  const years = useMemo(() => yearTotals(points), [points]);
  const ranking = useMemo(() => tornado(planning, market, season, lever), [planning, market, season, lever]);
  const seasonName = SEASON_NAMES[season]?.toLowerCase();
  const untouched = activePreset(input) === "today";
  const marketName = titleCase(market);

  const starts = points.filter((p) => p.week > weekly.last_actual_week && Number(p.week.slice(5, 7)) % 3 === 1 && Number(p.week.slice(8, 10)) <= 7);

  const isDomestic = market === "DOMESTIC";
  const presets = useMemo(() => PRESETS.map((p) => ({
    ...p,
    disabled: isDomestic && p.value === "more_flights",
  })), [isDomestic]);

  return (
    <div className="workbench">
      <aside className="workbench__panel" aria-label="Scenario settings">
        <Card>
          <ControlSection title="Where and when">
            <Select label="Market" value={market} onChange={setMarket} options={markets.map((m) => ({ value: m.value, label: titleCase(m.label) }))} />
            <Segmented label="Season" value={season} onChange={setSeason} options={seasons.map((s) => ({ value: s, label: SEASON_NAMES[s] ?? s }))} />
            <p className="note">{SEASON_MONTHS[season]}</p>
            {headline.result.is_cold_start && <Badge tone="neutral">No direct flights today, estimated from similar markets</Badge>}
          </ControlSection>
          <ControlSection title="Start from">
            <Chips label="Scenario presets" options={presets} value={activePreset(input)} onChange={(id) => dispatch({ type: "preset", id })} />
          </ControlSection>
          {LEVER_GROUPS.map((group) => {
            const isFlights = group.id === "flights";
            const sectionDisabled = isDomestic && isFlights;
            return (
              <ControlSection key={group.id} title={group.title} onReset={() => dispatch({ type: "resetGroup", group: group.id })} resetDisabled={sectionDisabled || !groupChanged(input, group)}>
                {sectionDisabled && <p className="note">UAE resident staycations do not use flight routes.</p>}
                {group.sliders.map((s) => {
                  const disabled = isDomestic ? (isFlights || s.key === "p2pPts") : (s.key === "gauge" && input.frequency === 0);
                  const hint = (s.key === "gauge" && input.frequency === 0)
                    ? "Applies when extra flights are added"
                    : (isDomestic && s.key === "p2pPts")
                    ? "Not applicable to domestic residents"
                    : s.hint;
                  return (
                    <SliderRow key={s.key} label={s.label} hint={hint} value={input[s.key]} defaultValue={DEFAULT_INPUT[s.key]}
                               min={s.min} max={s.max} step={s.step} format={s.format} disabled={disabled}
                               onChange={(value) => dispatch({ type: "set", key: s.key, value })} />
                  );
                })}
              </ControlSection>
            );
          })}
          <ControlSection title="Forecast" onReset={() => { setStart(weekly.last_actual_week); setGrowthPct(0); }}
                          resetDisabled={start === weekly.last_actual_week && growthPct === 0}>
            <div className="timeline__field">
              <span className="timeline__label">Changes start</span>
              <Select label="Week the changes start" value={start} onChange={setStart}
                      options={[{ value: weekly.last_actual_week, label: `${formatMonth(weekly.last_actual_week)} (after the latest data)` },
                                ...starts.map((p) => ({ value: p.week, label: formatMonth(p.week) }))]} />
            </div>
            <SliderRow label="Expected yearly growth" hint="Applies to multi-year timeline forecast. Without it the forecast stays flat." value={growthPct} defaultValue={0}
                       min={-5} max={10} step={0.5} format={(v) => `${formatSigned(v, String)}% a year`} onChange={setGrowthPct} />
          </ControlSection>
        </Card>
      </aside>

      <section className="workbench__canvas" aria-label="Scenario visual">
        <Card title={VIEWS.find((v) => v.value === view)!.label}
              actions={<Segmented label="Visual" value={view} onChange={setView} options={VIEWS} />}>
          {view === "map" && (
            <div className="canvas__body">
              <p className="note">Press play to watch the weeks go by, from the past into the forecast. Click a market to pick it.</p>
              <MapPlayback key={`${start}`} pb={pb} selected={market} startWeek={start} onSelect={setMarket} />
            </div>
          )}
          {view === "time" && (
            <TimelinePanel weekly={weekly} points={points} error={holdoutWmape(points)} start={start} />
          )}
          {view === "chain" && (
            <div className="canvas__split">
              <ChainTable headline={headline} />
              <Waterfall steps={[
                { label: "Today", value: headline.base, total: true },
                { label: "Seats", value: headline.result.waterfall.seats },
                { label: "Fuller", value: headline.result.waterfall.lf },
                { label: "Stopovers", value: headline.result.waterfall.p2p },
                { label: "Bookings", value: headline.result.waterfall.multiplier },
                { label: "Per visitor", value: headline.result.waterfall.los },
                { label: "With changes", value: headline.sim, total: true },
              ]} />
            </div>
          )}
          {view === "levers" && (
            <div className="canvas__body">
              <p className="note">Weekly guests gained or lost when each lever moves one typical step down or up, {marketName} in {seasonName}.</p>
              <Tornado rows={ranking.map((r) => ({ label: leverName(r.lever_name), low: r.low_impact_delta, high: r.high_impact_delta }))} />
            </div>
          )}
        </Card>
      </section>

      <aside className="workbench__results" aria-label="Results">
        <StatCard title="Hotel guests per week today" tone="neutral" value={formatFull(headline.base)} caption={`${marketName}, ${seasonName} average`} />
        <StatCard title="With your changes" tone="accent" value={formatFull(headline.sim)} caption={`Estimate, ±${Math.round(headline.errorPct * 100)}% error`} />
        <StatCard title="Difference" tone="secondary" value={<span className={toneOf(headline.change)}>{formatSigned(headline.change)}</span>}
                  caption={untouched ? "Nothing changed yet" : headline.changePct === null ? "No flights today to compare with" : `${formatPercent(headline.changePct)} guests per week`} />
        {untouched ? (
          <Card title="Your scenario">
            <p className="note">Move a slider or pick a starting point on the left. The numbers here show what your changes add, week by week and year by year.</p>
          </Card>
        ) : years.length > 0 ? (
          <Card title="Extra guests per year" subtitle={`From ${formatMonth(start)}, when your changes start`}>
            <table className="table">
              <thead><tr><th scope="col">Year</th><th scope="col">Extra guests</th></tr></thead>
              <tbody>
                {years.map((y) => (
                  <tr key={y.year}>
                    <th scope="row">{y.year}{y.weeks < 52 ? ` (${y.weeks} wk)` : ""}</th>
                    <td className={toneOf(y.scenario - y.model)}>{formatSigned(y.scenario - y.model)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        ) : (
          <Card title="Estimated impact">
            <p className="note">New service impact is estimated from archetype priors. Multi-year timeline projections are available for markets with historical flight schedules.</p>
          </Card>
        )}
        <p className="note">Estimates from past flight and hotel data, not guarantees. In past checks, real weeks landed within the stated error about 2 weeks in 3.</p>
      </aside>

      <div className="workbench__bar" aria-hidden="true">
        <span>{marketName}, {seasonName}</span>
        <strong className={toneOf(headline.change)}>{formatSigned(headline.change)} guests a week</strong>
      </div>
    </div>
  );
}

const ROWS: ReadonlyArray<{ label: string; key: keyof SimulationResult["base"]; kind: "count" | "share" | "ratio" }> = [
  { label: "Seats per week", key: "seats", kind: "count" },
  { label: "× share of seats sold", key: "lf", kind: "share" },
  { label: "= passengers", key: "pax", kind: "count" },
  { label: "× share who stop in Abu Dhabi", key: "p2pShare", kind: "share" },
  { label: "= visitors arriving", key: "p2p", kind: "count" },
  { label: "× hotel booking rate", key: "multiplier", kind: "ratio" },
  { label: "= hotel check-ins", key: "arrivals", kind: "count" },
  { label: "× guests per visitor", key: "los", kind: "ratio" },
  { label: "= guests from flights", key: "guests", kind: "count" },
];

function ChainTable({ headline }: { headline: WeeklyHeadline }) {
  const { result } = headline;
  const show = (value: number, kind: "count" | "share" | "ratio") =>
    kind === "count" ? formatFull(value) : kind === "share" ? `${(value * 100).toFixed(1)}%` : value.toFixed(2);
  return (
    <table className="table">
      <thead><tr><th scope="col">Step</th><th scope="col">Today</th><th scope="col">With changes</th></tr></thead>
      <tbody>
        {ROWS.map((row) => {
          const base = result.base[row.key], sim = result.sim[row.key];
          return (
            <tr key={row.key} className={row.label.startsWith("=") ? "table__row--emphasis" : undefined}>
              <th scope="row">{row.label}</th>
              <td>{show(base, row.kind)}</td>
              <td className={Math.abs(sim - base) > 1e-9 ? toneOf(sim - base) : undefined}>{show(sim, row.kind)}</td>
            </tr>
          );
        })}
        <tr><th scope="row">+ holidays and calendar</th><td>{formatSigned(headline.residual)}</td><td>{formatSigned(headline.residual)}</td></tr>
        <tr className="table__row--emphasis table__row--total">
          <th scope="row">= hotel guests per week</th><td>{formatFull(headline.base)}</td>
          <td className={toneOf(headline.change)}>{formatFull(headline.sim)}</td>
        </tr>
      </tbody>
    </table>
  );
}
