import { Tornado } from "../../components/charts/Tornado";
import { Waterfall, type WaterfallStep } from "../../components/charts/Waterfall";
import { Segmented } from "../../components/ui";
import { leverNameWithStep, SEASON_MONTHS, SEASON_NAMES, marketName } from "../../content/labels";
import { formatFull, formatSigned, toneOf } from "../../data/format";
import { tornado, weeklyHeadline, type Lever, type Planning, type SimulationResult, type WeeklyHeadline } from "../../engine/planning";

/** The two season-level views ("How it adds up", "Biggest levers"): one market, one season. */
interface SeasonViewProps { planning: Planning; market: string; lever: Lever; season: string; seasons: string[]; onSeason: (s: string) => void }

function SeasonPicker({ season, seasons, onSeason }: Pick<SeasonViewProps, "season" | "seasons" | "onSeason">) {
  return (
    <div className="season-picker">
      <Segmented label="Season" value={season} onChange={onSeason} options={seasons.map((s) => ({ value: s, label: SEASON_NAMES[s] ?? s }))} />
      <span className="note">{SEASON_MONTHS[season]}, an average week</span>
    </div>
  );
}

export function ChainView(props: SeasonViewProps) {
  const headline = weeklyHeadline(props.planning, props.market, props.season, props.lever);
  const isDomestic = props.market === "DOMESTIC";
  const steps: WaterfallStep[] = isDomestic
    ? [
        { label: "Today", value: headline.base, total: true },
        { label: "Bookings", value: headline.result.waterfall.multiplier },
        { label: "Per visitor", value: headline.result.waterfall.los },
        { label: "With changes", value: headline.sim, total: true },
      ]
    : [
        { label: "Today", value: headline.base, total: true },
        { label: "Seats", value: headline.result.waterfall.seats },
        { label: "Fuller", value: headline.result.waterfall.lf },
        { label: "Stopovers", value: headline.result.waterfall.p2p },
        { label: "Bookings", value: headline.result.waterfall.multiplier },
        { label: "Per visitor", value: headline.result.waterfall.los },
        { label: "With changes", value: headline.sim, total: true },
      ];
  const hasChanges = Math.abs(headline.change) > 1e-4;
  const activeSteps = steps.filter((s) => s.total || Math.abs(s.value) >= 0.5);

  return (
    <div className="canvas__body">
      <SeasonPicker {...props} />
      <div className="canvas__split">
        <ChainTable headline={headline} />
        <div>
          <Waterfall steps={activeSteps} />
          {!hasChanges && (
            <p className="note" style={{ textAlign: "center", marginTop: 4 }}>
              Baseline: adjust sliders on the left (e.g. flights, booking rate) to see the waterfall steps.
            </p>
          )}
        </div>
      </div>
      <p className="note">
        Hotel nights per week for {marketName(props.market)}, estimate ±{Math.round(headline.errorPct * 100)}% error.
        {isDomestic ? " UAE residents drive or travel locally; stays do not depend on flights." : ""}
      </p>
    </div>
  );
}

export function LeversView(props: SeasonViewProps) {
  const ranking = tornado(props.planning, props.market, props.season, props.lever);
  const isDomestic = props.market === "DOMESTIC";
  const rows = ranking
    .filter((r) => Math.abs(r.swing_spread) > 1e-6)
    .map((r) => ({
      label: leverNameWithStep(r.lever_name),
      low: r.low_impact_delta,
      high: r.high_impact_delta,
    }));
  return (
    <div className="canvas__body">
      <SeasonPicker {...props} />
      <p className="note">
        {isDomestic
          ? `Hotel nights a week gained or lost when each lever moves one typical step down or up, ${marketName(props.market)}. UAE residents' stays do not depend on flights.`
          : `Hotel nights a week gained or lost when each lever moves one typical step down or up, ${marketName(props.market)}.`}
      </p>
      <Tornado rows={rows} />
    </div>
  );
}

const INTERNATIONAL_ROWS: ReadonlyArray<{ label: string; key: keyof SimulationResult["base"]; kind: "count" | "share" | "ratio" }> = [
  { label: "Seats per week", key: "seats", kind: "count" },
  { label: "× share of seats sold", key: "lf", kind: "share" },
  { label: "= passengers", key: "pax", kind: "count" },
  { label: "× share who stop in Abu Dhabi", key: "p2pShare", kind: "share" },
  { label: "= visitors arriving", key: "p2p", kind: "count" },
  { label: "× hotel arrival multiplier", key: "multiplier", kind: "ratio" },
  { label: "= hotel check-ins", key: "arrivals", kind: "count" },
  { label: "× hotel nights per visitor", key: "los", kind: "ratio" },
  { label: "= hotel nights from flights", key: "guests", kind: "count" },
];

const DOMESTIC_ROWS: ReadonlyArray<{ label: string; key: keyof SimulationResult["base"]; kind: "count" | "share" | "ratio" }> = [
  { label: "Baseline hotel check-ins", key: "arrivals", kind: "count" },
  { label: "× booking response factor", key: "multiplier", kind: "ratio" },
  { label: "= hotel check-ins", key: "arrivals", kind: "count" },
  { label: "× hotel nights per visitor", key: "los", kind: "ratio" },
  { label: "= hotel nights (domestic stays)", key: "guests", kind: "count" },
];

function ChainTable({ headline }: { headline: WeeklyHeadline }) {
  const { result } = headline;
  const isDomestic = result.market === "DOMESTIC";
  const rows = isDomestic ? DOMESTIC_ROWS : INTERNATIONAL_ROWS;
  const show = (value: number, kind: "count" | "share" | "ratio") =>
    kind === "count" ? formatFull(value) : kind === "share" ? `${(value * 100).toFixed(1)}%` : value.toFixed(2);
  return (
    <table className="table">
      <thead><tr><th scope="col">Step</th><th scope="col">Today</th><th scope="col">With changes</th></tr></thead>
      <tbody>
        {rows.map((row, idx) => {
          const base = result.base[row.key];
          const sim = isDomestic && idx === 0 ? base : result.sim[row.key];
          return (
            <tr key={`${row.key}-${idx}`} className={row.label.startsWith("=") ? "table__row--emphasis" : undefined}>
              <th scope="row">{row.label}</th>
              <td>{show(base, row.kind)}</td>
              <td className={Math.abs(sim - base) > 1e-9 ? toneOf(sim - base) : undefined}>{show(sim, row.kind)}</td>
            </tr>
          );
        })}
        <tr><th scope="row">+ holidays and calendar</th><td>{formatSigned(headline.residual)}</td><td>{formatSigned(headline.residual)}</td></tr>
        <tr className="table__row--emphasis table__row--total">
          <th scope="row">= hotel nights per week</th><td>{formatFull(headline.base)}</td>
          <td className={toneOf(headline.change)}>{formatFull(headline.sim)}</td>
        </tr>
      </tbody>
    </table>
  );
}
