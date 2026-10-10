import { useMemo, useState } from "react";
import { BarCompare } from "../../components/charts/BarCompare";
import { TrendBand } from "../../components/charts/TrendBand";
import { PageLayout } from "../../components/layout/PageLayout";
import { Card, Segmented } from "../../components/ui";
import { formatPercent, titleCase, toneOf } from "../../data/format";
import { AGGREGATES, bucketBars, changeVsLastYear, nowcastView, type NowcastInput } from "../../engine/nowcastViews";
import type { Bundle } from "../../engine/types";
import { ControlsPanel } from "./ControlsPanel";
import { NationalityList } from "./NationalityList";
import { RangeCards } from "./RangeCards";
import "./dashboard.css";

type Grain = "day" | "week";

export function Dashboard({ bundle, search }: { bundle: Bundle; search: string }) {
  const seriesNames = useMemo(() => [...AGGREGATES, ...Object.keys(bundle.nowcast.series).filter((n) => !(AGGREGATES as readonly string[]).includes(n)).sort()], [bundle]);
  const [input, setInput] = useState<NowcastInput>({ series: "TOTAL", startIndex: 0, length: 28, domestic: 1, international: 1, market: 1 });
  const [grain, setGrain] = useState<Grain>("week");
  const view = useMemo(() => nowcastView(bundle, input), [bundle, input]);
  const bars = useMemo(() => bucketBars(view, grain), [view, grain]);
  const yoy = changeVsLastYear(bars);
  const { from, to } = view.window;
  const trend = view.dates.slice(from, to + 1).map((date, k) => ({ date, pred: view.pred[from + k], band: view.band[from + k], whatIf: view.whatIf[from + k] }));

  return (
    <PageLayout asideLabel="Forecast settings" aside={<ControlsPanel input={input} seriesNames={seriesNames} dates={view.dates} onChange={setInput} />}>
      <RangeCards predicted={view.predicted} scenario={view.scenario} changed={view.changed}
                  days={to - from + 1} start={view.dates[from]} end={view.dates[to]} />
      <div className="page__row">
        <Card title="Compared with last year"
              subtitle={yoy === null ? `${titleCase(input.series)}: no data a year earlier` : <><strong className={toneOf(yoy)}>{formatPercent(yoy)}</strong> vs the same days last year</>}
              actions={<Segmented label="Show by" options={[{ value: "day", label: "Days" }, { value: "week", label: "Weeks" }]} value={grain} onChange={setGrain} />}>
          <BarCompare data={bars} currentLabel={view.changed ? "With your changes" : "Forecast"} comparisonLabel="Last year" />
        </Card>
        <Card title="Hotel guests per day" subtitle="Shaded: the likely range">
          <TrendBand data={trend} showWhatIf={view.changed} />
        </Card>
      </div>
      <NationalityList nowcast={bundle.nowcast} start={view.dates[from]} end={view.dates[to]} filter={search} />
    </PageLayout>
  );
}
