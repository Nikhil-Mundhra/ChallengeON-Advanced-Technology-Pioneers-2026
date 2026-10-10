import { Card, Segmented, Select, Slider } from "../../components/ui";
import { formatPercent, titleCase } from "../../data/format";
import type { ScenarioInput } from "./useScenario";

const LENGTHS = [{ value: "7", label: "7 days" }, { value: "14", label: "14 days" }, { value: "28", label: "28 days" }, { value: "91", label: "3 months" }] as const;
const COVERAGES = [{ value: "0.5", label: "50%" }, { value: "0.8", label: "80%" }, { value: "0.9", label: "90%" }] as const;

interface ControlsProps {
  input: ScenarioInput;
  seriesNames: string[];
  dates: string[];
  onChange: (input: ScenarioInput) => void;
}

const factor = (value: number) => formatPercent(value - 1, 0);

/** Left panel: what to look at (series, range, interval) and the arrivals what-if sliders. */
export function ControlsPanel({ input, seriesNames, dates, onChange }: ControlsProps) {
  const set = (patch: Partial<ScenarioInput>) => onChange({ ...input, ...patch });
  const isMarket = input.series !== "TOTAL" && input.series !== "INTERNATIONAL";
  return (
    <aside className="controls" aria-label="Scenario controls">
      <Card title="View">
        <Select label="Series" value={input.series} onChange={(series) => set({ series, market: 1 })}
                options={seriesNames.map((name) => ({ value: name, label: titleCase(name) }))} />
        <Segmented label="Range length" options={LENGTHS} value={String(input.length) as (typeof LENGTHS)[number]["value"]}
                   onChange={(value) => set({ length: Number(value) })} />
        <Slider label="Range starts" value={input.startIndex} min={0} max={Math.max(dates.length - input.length, 0)}
                format={(i) => dates[i] ?? ""} onChange={(startIndex) => set({ startIndex })} />
        <div>
          <p className="controls__hint">Interval</p>
          <Segmented label="Interval coverage" options={COVERAGES} value={input.coverage as "0.5" | "0.8" | "0.9"}
                     onChange={(coverage) => set({ coverage })} />
        </div>
      </Card>
      <Card title="What-if: arrivals" subtitle="Change hotel new arrivals over the predicted period">
        <Slider label="Domestic" value={input.domestic} min={0.5} max={1.5} step={0.01} format={factor} onChange={(domestic) => set({ domestic })} />
        <Slider label="International" value={input.international} min={0.5} max={1.5} step={0.01} format={factor} onChange={(international) => set({ international })} />
        {isMarket && <Slider label={titleCase(input.series)} value={input.market} min={0} max={2} step={0.01} format={factor} onChange={(market) => set({ market })} />}
        <button type="button" className="button" onClick={() => set({ domestic: 1, international: 1, market: 1 })}>Reset</button>
      </Card>
    </aside>
  );
}
