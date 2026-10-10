import { useMemo, useState } from "react";
import { Tornado } from "../../components/charts/Tornado";
import { Waterfall } from "../../components/charts/Waterfall";
import { Badge, Card, Segmented, Select, Slider, Stat } from "../../components/ui";
import { formatCount, formatFull, formatPercent, titleCase } from "../../data/format";
import { conformalBands, hybrid, simulate, tornado, type Planning, type SimulationResult } from "../../engine/planning";
import type { Weekly } from "../../engine/weekly";
import { DEFAULT_INPUT, LEVER_SLIDERS, marketOptions, toLever, type LeverInput } from "./levers";
import { TimelineCard } from "./TimelineCard";
import "./simulate.css";

/** Flight scenario simulator: levers on the left; on the right the season-level scenario, the
 *  weekly back-test and multi-year projection, the conversion chain, its attribution and lever
 *  sensitivity. Everything is computed in the browser by
 *  engine/planning.ts from the exported calibration. */
export function SimulatePage({ planning, weekly }: { planning: Planning; weekly: Weekly }) {
  const markets = useMemo(() => marketOptions(planning), [planning]);
  const seasons = useMemo(() => Object.keys(Object.values(planning.calibration)[0]), [planning]);
  const [market, setMarket] = useState("UNITED KINGDOM");
  const [season, setSeason] = useState(seasons[0]);
  const [input, setInput] = useState<LeverInput>(DEFAULT_INPUT);
  const [start, setStart] = useState(weekly.last_actual_week);
  const [growthPct, setGrowthPct] = useState(0);

  const lever = useMemo(() => toLever(input), [input]);
  const result = simulate(planning, market, season, lever);
  const calendar = hybrid(planning, result);
  const band = conformalBands(planning, result);
  const sensitivity = useMemo(() => tornado(planning, market, season, lever), [planning, market, season, lever]);
  const lift = result.base.guests > 0 ? result.delta_guests / result.base.guests : null;

  return (
    <div className="simulate">
      <aside className="controls" aria-label="Scenario levers">
        <Card title="Market and season">
          <Select label="Market" value={market} onChange={setMarket}
                  options={markets.map((m) => ({ value: m.value, label: titleCase(m.label) }))} />
          <Segmented label="Season" value={season} onChange={setSeason}
                     options={seasons.map((s) => ({ value: s, label: s.split("_")[0] }))} />
          {result.is_cold_start && <Badge tone="neutral">Cold start: archetype defaults, no flights in the data</Badge>}
        </Card>
        <Card title="Levers" actions={<button type="button" className="button" onClick={() => setInput(DEFAULT_INPUT)}>Reset</button>}>
          {LEVER_SLIDERS.map((s) => (
            <Slider key={s.key} label={s.label} value={input[s.key]} min={s.min} max={s.max} step={s.step} format={s.format}
                    onChange={(value) => setInput((prev) => ({ ...prev, [s.key]: value }))} />
          ))}
        </Card>
      </aside>

      <div className="simulate__main">
        <div className="simulate__stats">
          <Card title="Current weekly guests" className="stat-card stat-card--neutral">
            <Stat value={formatFull(calendar.base)} caption={`structural ${formatCount(result.base.guests)} + calendar residual ${formatCount(calendar.residual)}`} />
          </Card>
          <Card title="Scenario weekly guests" className="stat-card stat-card--accent">
            <Stat value={formatFull(calendar.sim)} caption={`structural band ${formatCount(band.p10)}–${formatCount(band.p90)} (±${Math.round(band.margin * 100)}%)`} />
          </Card>
          <Card title="Change" className="stat-card stat-card--secondary">
            <Stat value={<span className={result.delta_guests >= 0 ? "up" : "down"}>{result.delta_guests >= 0 ? "+" : ""}{formatFull(result.delta_guests)}</span>}
                  caption={lift === null ? "no current service" : `${formatPercent(lift)} · band ${formatCount(band.deltaP10)} to ${formatCount(band.deltaP90)}`} />
          </Card>
        </div>

        <TimelineCard planning={planning} weekly={weekly} market={market} lever={lever} start={start} growthPct={growthPct}
                      onStart={setStart} onGrowth={setGrowthPct} />

        <div className="simulate__row">
          <Card title="Conversion chain" subtitle="One factor per link; the scenario edits the factors you move">
            <ChainTable result={result} />
          </Card>
          <Card title="Where the change comes from" subtitle="Step-by-step attribution; the parts sum to the change exactly">
            <Waterfall steps={[
              { label: "Current", value: result.base.guests, total: true },
              { label: "Seats", value: result.waterfall.seats },
              { label: "Load f.", value: result.waterfall.lf },
              { label: "P2P", value: result.waterfall.p2p },
              { label: "Mult.", value: result.waterfall.multiplier },
              { label: "Per arrival", value: result.waterfall.los },
              { label: "Scenario", value: result.sim.guests, total: true },
            ]} />
          </Card>
        </div>

        <Card title="Which lever moves demand most" subtitle={`Weekly guests when each lever moves down and up, ${titleCase(market)}, ${season.replace("_", " ")}`}>
          <Tornado rows={sensitivity.map((r) => ({ label: r.lever_name.replace(/ \(.*\)$/, ""), low: r.low_impact_delta, high: r.high_impact_delta }))} />
        </Card>

        <p className="simulate__note">
          Bands are conformal margins from 30 holdout weeks; they covered {band.coverage.toFixed(1)}% of weeks against an 80% target, so read them as too narrow.
          Planning estimates from observational data, not causal effects.
        </p>
      </div>
    </div>
  );
}

const ROWS: ReadonlyArray<{ label: string; key: keyof SimulationResult["base"]; kind: "count" | "share" | "ratio" }> = [
  { label: "Weekly seats", key: "seats", kind: "count" },
  { label: "× load factor", key: "lf", kind: "share" },
  { label: "= passengers", key: "pax", kind: "count" },
  { label: "× point-to-point share", key: "p2pShare", kind: "share" },
  { label: "= P2P passengers", key: "p2p", kind: "count" },
  { label: "× response multiplier", key: "multiplier", kind: "ratio" },
  { label: "= hotel arrivals", key: "arrivals", kind: "count" },
  { label: "× guests per arrival", key: "los", kind: "ratio" },
  { label: "= weekly guests", key: "guests", kind: "count" },
];

function ChainTable({ result }: { result: SimulationResult }) {
  const show = (value: number, kind: "count" | "share" | "ratio") =>
    kind === "count" ? formatFull(value) : kind === "share" ? `${(value * 100).toFixed(1)}%` : value.toFixed(2);
  return (
    <table className="chain">
      <thead><tr><th scope="col">Link</th><th scope="col">Current</th><th scope="col">Scenario</th></tr></thead>
      <tbody>
        {ROWS.map((row) => {
          const base = result.base[row.key], sim = result.sim[row.key];
          const changed = Math.abs(sim - base) > 1e-9;
          return (
            <tr key={row.key} className={row.label.startsWith("=") ? "chain__stock" : undefined}>
              <th scope="row">{row.label}</th>
              <td>{show(base, row.kind)}</td>
              <td className={changed ? (sim > base ? "up" : "down") : undefined}>{show(sim, row.kind)}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
