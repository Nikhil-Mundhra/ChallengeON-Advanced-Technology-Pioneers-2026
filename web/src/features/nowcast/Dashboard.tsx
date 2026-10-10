import { useMemo, useState } from "react";
import { BarCompare, type BarPoint } from "../../components/charts/BarCompare";
import { TrendBand } from "../../components/charts/TrendBand";
import { Card, Segmented } from "../../components/ui";
import { formatPercent, titleCase } from "../../data/format";
import type { Bundle } from "../../engine/types";
import { ControlsPanel } from "./ControlsPanel";
import { NationalityList } from "./NationalityList";
import { RangeCards } from "./RangeCards";
import { AGGREGATES, useScenario, type ScenarioInput } from "./useScenario";
import "./dashboard.css";

type Grain = "day" | "week";

export function Dashboard({ bundle, search }: { bundle: Bundle; search: string }) {
  const seriesNames = useMemo(() => [...AGGREGATES, ...Object.keys(bundle.nowcast.series).filter((n) => !(AGGREGATES as readonly string[]).includes(n)).sort()], [bundle]);
  const [input, setInput] = useState<ScenarioInput>({ series: "TOTAL", startIndex: 0, length: 28, coverage: String(bundle.manifest.coverage), domestic: 1, international: 1, market: 1 });
  const [grain, setGrain] = useState<Grain>("week");
  const scenario = useScenario(bundle, input);
  const end = Math.min(input.startIndex + input.length, scenario.dates.length) - 1;
  const window = { from: input.startIndex, to: end };

  const bars: BarPoint[] = useMemo(() => {
    const step = grain === "week" ? 7 : 1;
    const points: BarPoint[] = [];
    for (let i = window.from; i <= window.to; i += step) {
      const stop = Math.min(i + step - 1, window.to);
      let current = 0; let comparison: number | null = 0;
      for (let t = i; t <= stop; t += 1) {
        current += input.domestic !== 1 || input.international !== 1 || input.market !== 1 ? scenario.whatIf[t] : scenario.pred[t];
        const last = scenario.lastYear[t];
        comparison = comparison === null || last === null ? null : comparison + last;
      }
      points.push({ label: scenario.dates[i].slice(5), current, comparison });
    }
    return points;
  }, [scenario, grain, window.from, window.to, input.domestic, input.international, input.market]);

  const trend = scenario.dates.slice(window.from, window.to + 1).map((date, k) => {
    const t = window.from + k;
    return { date, pred: scenario.pred[t], band: scenario.band[t], whatIf: scenario.whatIf[t] };
  });
  const yoy = useMemo(() => {
    const known = bars.filter((b) => b.comparison !== null);
    const now = known.reduce((s, b) => s + b.current, 0); const then = known.reduce((s, b) => s + (b.comparison ?? 0), 0);
    return then ? now / then - 1 : null;
  }, [bars]);

  return (
    <div className="dashboard">
      <ControlsPanel input={input} seriesNames={seriesNames} dates={scenario.dates} onChange={setInput} />
      <div className="dashboard__main">
        <RangeCards predicted={scenario.predicted} scenario={scenario.scenario} changed={scenario.changed}
                    coverage={input.coverage} days={end - input.startIndex + 1} />
        <div className="dashboard__row">
          <Card title="Overview" className="dashboard__wide"
                subtitle={yoy === null ? `${titleCase(input.series)} · no year-earlier data` : <><strong className={yoy >= 0 ? "up" : "down"}>{formatPercent(yoy)}</strong> vs the same days a year earlier</>}
                actions={<Segmented label="Bar grain" options={[{ value: "day", label: "Days" }, { value: "week", label: "Weeks" }]} value={grain} onChange={setGrain} />}>
            <BarCompare data={bars} currentLabel={scenario.changed ? "What-if" : "Predicted"} comparisonLabel="A year earlier" />
          </Card>
          <Card title="Daily guests" subtitle={`${Math.round(Number(input.coverage) * 100)}% interval band`}>
            <TrendBand data={trend} showWhatIf={scenario.changed} />
          </Card>
        </div>
        <NationalityList nowcast={bundle.nowcast} start={scenario.dates[window.from]} end={scenario.dates[window.to]} filter={search} />
      </div>
    </div>
  );
}
