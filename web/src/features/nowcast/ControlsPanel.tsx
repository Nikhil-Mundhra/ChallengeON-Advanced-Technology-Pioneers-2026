import { Card, ControlSection, Segmented, Select, SliderRow } from "../../components/ui";
import { formatPercent, titleCase } from "../../data/format";
import type { NowcastInput } from "../../engine/nowcastViews";

const LENGTHS = [{ value: "7", label: "7 days" }, { value: "14", label: "14 days" }, { value: "28", label: "28 days" }, { value: "91", label: "3 months" }] as const;
const factor = (value: number) => formatPercent(value - 1, 0);

/** Left panel: what to look at (market and days) and the hotel check-in sliders. */
export function ControlsPanel({ input, seriesNames, dates, onChange }: {
  input: NowcastInput; seriesNames: string[]; dates: string[]; onChange: (input: NowcastInput) => void;
}) {
  const set = (patch: Partial<NowcastInput>) => onChange({ ...input, ...patch });
  const isMarket = input.series !== "TOTAL" && input.series !== "INTERNATIONAL";
  const changed = input.domestic !== 1 || input.international !== 1 || input.market !== 1;
  return (
    <Card>
      <ControlSection title="What to show">
        <Select label="Market" value={input.series} onChange={(series) => set({ series, market: 1 })}
                options={seriesNames.map((name) => ({ value: name, label: titleCase(name) }))} />
        <Segmented label="Number of days" options={LENGTHS} value={String(input.length) as (typeof LENGTHS)[number]["value"]}
                   onChange={(value) => set({ length: Number(value) })} />
        <SliderRow label="First day" value={input.startIndex} defaultValue={0} min={0} max={Math.max(dates.length - input.length, 0)}
                   format={(i) => dates[i] ?? ""} onChange={(startIndex) => set({ startIndex })} />
      </ControlSection>
      <ControlSection title="What if check-ins change" onReset={() => set({ domestic: 1, international: 1, market: 1 })} resetDisabled={!changed}>
        <SliderRow label="UAE residents" value={input.domestic} defaultValue={1} min={0.5} max={1.5} step={0.01} format={factor} onChange={(domestic) => set({ domestic })} />
        <SliderRow label="International visitors" value={input.international} defaultValue={1} min={0.5} max={1.5} step={0.01} format={factor} onChange={(international) => set({ international })} />
        {isMarket && <SliderRow label={titleCase(input.series)} value={input.market} defaultValue={1} min={0} max={2} step={0.01} format={factor} onChange={(market) => set({ market })} />}
      </ControlSection>
    </Card>
  );
}
