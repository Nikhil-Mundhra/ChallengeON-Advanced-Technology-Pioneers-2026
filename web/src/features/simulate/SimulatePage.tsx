import { marketName } from "../../content/labels";
import { useEffect, useMemo, useReducer, useState } from "react";
import { Card, Segmented } from "../../components/ui";
import { formatCount, formatSigned, toneOf } from "../../data/format";
import { simulate, type Planning } from "../../engine/planning";
import { playback } from "../../engine/playback";
import { holdoutWmape, timeline, totalTimeline, type Weekly } from "../../engine/weekly";
import { ALL_MARKETS, DEFAULT_INPUT, leverReducer, marketOptions, toLever } from "./levers";
import { LeverPanel } from "./LeverPanel";
import { MapPlayback } from "./MapPlayback";
import { NewRouteCard } from "./NewRouteCard";
import { ResultsPanel } from "./ResultsPanel";
import { ChainView, LeversView } from "./SeasonViews";
import { TimelinePanel } from "./TimelinePanel";
import "./simulate.css";

const VIEWS = [
  { value: "map", label: "Map" }, { value: "time", label: "Over time" }, { value: "chain", label: "How it adds up" }, { value: "levers", label: "Biggest levers" },
] as const;
type View = (typeof VIEWS)[number]["value"];

/** Flight scenario workbench: holds the shared state (market, levers, the week on the map) and
 *  lays out the three panes. Each pane is its own component; numbers come from src/engine. */
export function SimulatePage({ planning, weekly }: { planning: Planning; weekly: Weekly }) {
  const markets = useMemo(() => marketOptions(planning), [planning]);
  const seasons = useMemo(() => Object.keys(Object.values(planning.calibration)[0]), [planning]);
  const [market, setMarket] = useState(ALL_MARKETS);
  const [season, setSeason] = useState(seasons[0]);
  const [input, dispatch] = useReducer(leverReducer, DEFAULT_INPUT);
  const [view, setView] = useState<View>("map");
  const firstWeek = useMemo(() => {   // the first week after the real data: changes start here by default
    const weeks = Object.values(weekly.markets)[0].week;
    return weeks[weeks.indexOf(weekly.last_actual_week) + 1] ?? weekly.last_actual_week;
  }, [weekly]);
  const [start, setStart] = useState(firstWeek);
  const [growthPct, setGrowthPct] = useState(0);

  const all = market === ALL_MARKETS;
  const lever = useMemo(() => toLever(all ? DEFAULT_INPUT : input), [input, all]);
  const options = { start, growthPct };
  const pb = useMemo(() => playback(planning, weekly, market, lever, options), [planning, weekly, market, lever, start, growthPct]);   // eslint-disable-line react-hooks/exhaustive-deps
  const points = useMemo(() => (all ? totalTimeline(planning, weekly, market, lever, options) : timeline(planning, weekly, market, lever, options)),
    [planning, weekly, market, lever, start, growthPct, all]);   // eslint-disable-line react-hooks/exhaustive-deps
  const [week, setWeek] = useState(() => Math.max(0, pb.weeks.indexOf(start)));
  useEffect(() => setWeek(Math.max(0, pb.weeks.indexOf(start))), [start]);   // eslint-disable-line react-hooks/exhaustive-deps

  const startOptions = pb.weeks.filter((w) => w > firstWeek && Number(w.slice(5, 7)) % 3 === 1 && Number(w.slice(8, 10)) <= 7);
  const coldStart = !all && simulate(planning, market, seasons[0]).is_cold_start;
  const sel = all ? undefined : pb.markets[market];
  const weekChange = sel ? sel.extra[week] : 0;

  return (
    <div className="workbench">
      <aside className="workbench__panel" aria-label="Scenario settings">
        <LeverPanel markets={markets} market={market} onMarket={setMarket} coldStart={coldStart} input={input} dispatch={dispatch}
                    start={start} startOptions={startOptions} onStart={setStart} defaultStart={firstWeek}
                    growthPct={growthPct} onGrowth={setGrowthPct} />
      </aside>

      <section className="workbench__canvas" aria-label="Scenario visual">
        <Card title={VIEWS.find((v) => v.value === view)!.label} actions={<Segmented label="Visual" value={view} onChange={setView} options={VIEWS} />}>
          {view === "map" && (
            <div className="canvas__body">
              <p className="note">Press play to watch the weeks go by, from the past into the forecast. Click a market to pick it.</p>
              <MapPlayback pb={pb} selected={market} week={week} onWeek={setWeek} onSelect={setMarket} />
            </div>
          )}
          {view === "time" && <TimelinePanel weekly={weekly} points={points} error={holdoutWmape(points)} start={start} />}
          {(view === "chain" || view === "levers") && (all
            ? <p className="note">Pick a market on the left or on the map to see how its flights turn into hotel guests.</p>
            : view === "chain"
              ? <ChainView planning={planning} market={market} lever={lever} season={season} seasons={seasons} onSeason={setSeason} />
              : <LeversView planning={planning} market={market} lever={lever} season={season} seasons={seasons} onSeason={setSeason} />)}
        </Card>
      </section>

      <aside className="workbench__results" aria-label="Results">
        {!all && !pb.markets[market] && <NewRouteCard planning={planning} market={market} lever={lever} seasons={seasons} />}
        <ResultsPanel pb={pb} week={week} market={market} />
        <p className="note">Estimates from past flight and hotel data, not guarantees.</p>
      </aside>

      <div className="workbench__bar" aria-hidden="true">
        <span>{marketName(market)}</span>
        <strong className={toneOf(weekChange)}>{all ? `${formatCount(pb.total[week])} guests this week` : `${formatSigned(weekChange, formatCount)} guests this week`}</strong>
      </div>
    </div>
  );
}
