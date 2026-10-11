import { marketName } from "../../content/labels";
import { useEffect, useMemo, useReducer, useRef, useState } from "react";
import { useSearchParams } from "react-router";
import { Card, Segmented } from "../../components/ui";
import { formatCount, formatSigned, toneOf } from "../../data/format";
import { capacityOutlook } from "../../engine/capacity";
import { scheduleEffect, simulate, type Planning } from "../../engine/planning";
import { playback } from "../../engine/playback";
import { holdoutWmape, timeline, totalTimeline, type Weekly } from "../../engine/weekly";
import { ALL_MARKETS, DEFAULT_INPUT, leverReducer, marketOptions, scenarioFromQuery, scenarioQuery, startOptions, toLever } from "./levers";
import { LeverPanel } from "./LeverPanel";
import { MapPlayback } from "./MapPlayback";
import { NewRouteCard } from "./NewRouteCard";
import { ResizeGutter } from "./ResizeGutter";
import { ResultsPanel } from "./ResultsPanel";
import { ChainView, LeversView } from "./SeasonViews";
import { TimelinePanel } from "./TimelinePanel";
import "./simulate.css";

const DEFAULT_PANEL_WIDTH = 340;
const CAPACITY_YEARS = 3;   // the projection's length (export/bundle.PROJECTION_YEARS)
const DEFAULT_RESULTS_WIDTH = 300;

function readSavedWidth(key: string, fallback: number, min: number, max: number): number {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return fallback;
    const n = Number(raw);
    return Number.isFinite(n) && n >= min && n <= max ? n : fallback;
  } catch {
    return fallback;
  }
}

const VIEWS = [
  { value: "map", label: "Map" }, { value: "time", label: "Over time" }, { value: "chain", label: "How it adds up" }, { value: "levers", label: "Biggest levers" },
] as const;
type View = (typeof VIEWS)[number]["value"];

/** Flight scenario workbench: holds the shared state (market, levers, the week on the map) and
 *  lays out the three panes. Each pane is its own component; numbers come from src/engine.
 *  A link can carry a scenario with it (levers.scenarioQuery), so "try your own numbers" from a
 *  question card opens the workbench already filled with that card's example. */
export function SimulatePage({ planning, weekly }: { planning: Planning; weekly: Weekly }) {
  const markets = useMemo(() => marketOptions(planning), [planning]);
  const seasons = useMemo(() => Object.keys(Object.values(planning.calibration)[0]), [planning]);
  const weeks = useMemo(() => Object.values(weekly.markets)[0].week, [weekly]);
  const firstWeek = useMemo(() => weeks[weeks.indexOf(weekly.last_actual_week) + 1] ?? weekly.last_actual_week, [weeks, weekly]);
  const picks = useMemo(() => startOptions(weeks, firstWeek), [weeks, firstWeek]);
  const [search, setSearch] = useSearchParams();
  const opened = useMemo(() => scenarioFromQuery(search, { markets: markets.map((m) => m.value), seasons, starts: [firstWeek, ...picks] }),
    [search, markets, seasons, firstWeek, picks]);
  const [market, setMarket] = useState(opened.market);
  const [season, setSeason] = useState(opened.season ?? seasons[0]);
  const [input, dispatch] = useReducer(leverReducer, DEFAULT_INPUT, () => opened.input);
  const [start, setStart] = useState(opened.start ?? firstWeek);
  const [view, setView] = useState<View>("map");
  const [growthPct, setGrowthPct] = useState(0);

  const workbenchRef = useRef<HTMLDivElement>(null);
  const [panelWidth, setPanelWidth] = useState(() => readSavedWidth("workbench:panel_width", DEFAULT_PANEL_WIDTH, 260, 520));
  const [resultsWidth, setResultsWidth] = useState(() => readSavedWidth("workbench:results_width", DEFAULT_RESULTS_WIDTH, 240, 460));
  const [isResizing, setIsResizing] = useState(false);

  const updatePanelWidth = (w: number) => {
    setPanelWidth(w);
    try { localStorage.setItem("workbench:panel_width", String(w)); } catch {}
  };
  const resetPanelWidth = () => {
    setPanelWidth(DEFAULT_PANEL_WIDTH);
    try { localStorage.removeItem("workbench:panel_width"); } catch {}
  };
  const updateResultsWidth = (w: number) => {
    setResultsWidth(w);
    try { localStorage.setItem("workbench:results_width", String(w)); } catch {}
  };
  const resetResultsWidth = () => {
    setResultsWidth(DEFAULT_RESULTS_WIDTH);
    try { localStorage.removeItem("workbench:results_width"); } catch {}
  };

  const all = market === ALL_MARKETS;
  const lever = useMemo(() => toLever(all ? DEFAULT_INPUT : input), [input, all]);
  const capacityPct = all ? 0 : input.capacityPct;
  const options = { start, growthPct, capacityPct };
  const pb = useMemo(() => playback(planning, weekly, market, lever, options), [planning, weekly, market, lever, start, growthPct, capacityPct]);   // eslint-disable-line react-hooks/exhaustive-deps
  const points = useMemo(() => (all ? totalTimeline(planning, weekly, market, lever, options) : timeline(planning, weekly, market, lever, options)),
    [planning, weekly, market, lever, start, growthPct, capacityPct, all]);   // eslint-disable-line react-hooks/exhaustive-deps
  const schedule = all ? null : scheduleEffect(planning, market, season, lever);
  const capacity = { years: CAPACITY_YEARS, ...capacityOutlook(planning, capacityPct, CAPACITY_YEARS) };
  const [week, setWeek] = useState(() => Math.max(0, pb.weeks.indexOf(start)));
  useEffect(() => setWeek(Math.max(0, pb.weeks.indexOf(start))), [start]);   // eslint-disable-line react-hooks/exhaustive-deps

  // Lock page-level window scrolling on desktop so each pane scrolls cleanly internally.
  useEffect(() => {
    document.body.classList.add("body--workbench");
    return () => {
      document.body.classList.remove("body--workbench");
    };
  }, []);

  // The URL is the scenario: sharing or reloading the page keeps what is on screen.
  useEffect(() => {
    const query = scenarioQuery({ market, season, start: start === firstWeek ? undefined : start }, all ? DEFAULT_INPUT : input);
    if (query !== search.toString()) setSearch(query, { replace: true });
  }, [market, season, start, input, firstWeek, all, search, setSearch]);
  const coldStart = !all && simulate(planning, market, seasons[0]).is_cold_start;
  const sel = all ? undefined : pb.markets[market];
  const weekChange = sel ? sel.extra[week] : 0;

  return (
    <div
      ref={workbenchRef}
      className={`workbench${isResizing ? " workbench--resizing" : ""}`}
      style={{
        "--panel-width": `${panelWidth}px`,
        "--results-width": `${resultsWidth}px`,
      } as React.CSSProperties}
    >
      <aside className="workbench__panel" aria-label="Scenario settings">
        <LeverPanel markets={markets} market={market} onMarket={setMarket} coldStart={coldStart} input={input} dispatch={dispatch}
                    start={start} startOptions={picks} onStart={setStart} defaultStart={firstWeek}
                    growthPct={growthPct} onGrowth={setGrowthPct} season={season} schedule={schedule} capacity={capacity} />
      </aside>

      <ResizeGutter
        id="panel"
        label="Scenario settings width"
        value={panelWidth}
        defaultValue={DEFAULT_PANEL_WIDTH}
        min={260}
        max={520}
        onResize={updatePanelWidth}
        onReset={resetPanelWidth}
        workbenchRef={workbenchRef}
        onDragStateChange={setIsResizing}
      />

      <section className="workbench__canvas" aria-label="Scenario visual">
        <Card title={VIEWS.find((v) => v.value === view)!.label} actions={<Segmented label="Visual" value={view} onChange={setView} options={VIEWS} />}>
          {view === "map" && (
            <div className="canvas__body">
              <p className="note">Press play to watch the weeks go by, from the past into the forecast. Click a market to pick it.</p>
              <MapPlayback pb={pb} selected={market} week={week} onWeek={setWeek} onSelect={setMarket} />
            </div>
          )}
          {view === "time" && <TimelinePanel weekly={weekly} points={points} error={holdoutWmape(points)} start={start} />}
          {(view === "chain" || view === "levers") && (all ? (
            <div className="canvas__body">
              <p className="note">Pick a market on the left or on the map to see how its flights turn into hotel nights.</p>
            </div>
          ) : view === "chain" ? (
            <ChainView planning={planning} market={market} lever={lever} season={season} seasons={seasons} onSeason={setSeason} />
          ) : (
            <LeversView planning={planning} market={market} lever={lever} season={season} seasons={seasons} onSeason={setSeason} />
          ))}
        </Card>
      </section>

      <ResizeGutter
        id="results"
        label="Results panel width"
        value={resultsWidth}
        defaultValue={DEFAULT_RESULTS_WIDTH}
        min={240}
        max={460}
        onResize={updateResultsWidth}
        onReset={resetResultsWidth}
        workbenchRef={workbenchRef}
        onDragStateChange={setIsResizing}
      />

      <aside className="workbench__results" aria-label="Results">
        {!all && !pb.markets[market] && <NewRouteCard planning={planning} market={market} lever={lever} seasons={seasons} />}
        <ResultsPanel pb={pb} week={week} market={market} />
        <p className="note">Estimates from past flight and hotel data, not guarantees.</p>
      </aside>

      <div className="workbench__bar" aria-hidden="true">
        <span>{marketName(market)}</span>
        <strong className={toneOf(weekChange)}>{all ? `${formatCount(pb.total[week])} hotel nights this week` : `${formatSigned(weekChange, formatCount)} hotel nights this week`}</strong>
      </div>
    </div>
  );
}
