import { Tornado } from "../../components/charts/Tornado";
import { Waterfall } from "../../components/charts/Waterfall";
import { Segmented } from "../../components/ui";
import { leverName, SEASON_MONTHS, SEASON_NAMES, marketName } from "../../content/labels";
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
  return (
    <div className="canvas__body">
      <SeasonPicker {...props} />
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
      <p className="note">Weekly hotel guests for {marketName(props.market)}, estimate ±{Math.round(headline.errorPct * 100)}% error.</p>
    </div>
  );
}

export function LeversView(props: SeasonViewProps) {
  const ranking = tornado(props.planning, props.market, props.season, props.lever);
  return (
    <div className="canvas__body">
      <SeasonPicker {...props} />
      <p className="note">Weekly guests gained or lost when each lever moves one typical step down or up, {marketName(props.market)}.</p>
      <Tornado rows={ranking.map((r) => ({ label: leverName(r.lever_name), low: r.low_impact_delta, high: r.high_impact_delta }))} />
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
