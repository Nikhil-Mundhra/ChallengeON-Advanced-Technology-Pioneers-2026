import { marketName } from "../../content/labels";
import type { Dispatch } from "react";
import { Badge, Card, Chips, ControlSection, Select, SliderRow } from "../../components/ui";
import { formatMonth, formatSigned } from "../../data/format";
import { activePreset, ALL_MARKETS, DEFAULT_INPUT, groupChanged, LEVER_GROUPS, PRESETS, presetAvailable, sliderAvailability,
         type LeverAction, type LeverInput } from "./levers";

interface LeverPanelProps {
  markets: Array<{ value: string; label: string }>;
  market: string; onMarket: (m: string) => void; coldStart: boolean;
  input: LeverInput; dispatch: Dispatch<LeverAction>;
  start: string; startOptions: string[]; onStart: (w: string) => void; defaultStart: string;
  growthPct: number; onGrowth: (pct: number) => void;
}

/** Left panel: which market, a starting point, the flight and visitor levers, and forecast settings.
 *  Which levers apply to which market is decided in levers.ts (sliderAvailability). */
export function LeverPanel(p: LeverPanelProps) {
  const all = p.market === ALL_MARKETS;
  return (
    <Card>
      <ControlSection title="Market">
        <Select label="Market" value={p.market} onChange={p.onMarket}
                options={[{ value: ALL_MARKETS, label: "All markets" }, ...p.markets.map((m) => ({ value: m.value, label: m.label.endsWith("(no direct flights)") ? `${marketName(m.value)} (no direct flights)` : marketName(m.value) }))]} />
        {all && <p className="note">Pick a market here or on the map to try flight changes.</p>}
        {p.coldStart && <Badge tone="neutral">No direct flights today, estimated from similar markets</Badge>}
      </ControlSection>
      {!all && (
        <ControlSection title="Start from">
          <Chips label="Scenario presets" value={activePreset(p.input)} onChange={(id) => p.dispatch({ type: "preset", id })}
                 options={PRESETS.map((x) => ({ ...x, disabled: !presetAvailable(p.market, x.value) }))} />
        </ControlSection>
      )}
      {LEVER_GROUPS.map((group) => {
        const allOff = group.sliders.every((s) => sliderAvailability(p.market, p.input, s.key).disabled);
        return (
          <ControlSection key={group.id} title={group.title} onReset={() => p.dispatch({ type: "resetGroup", group: group.id })}
                          resetDisabled={allOff || !groupChanged(p.input, group)}>
            {p.market === "DOMESTIC" && group.id === "flights" && <p className="note">UAE residents' stays do not depend on flights.</p>}
            {group.sliders.map((s) => {
              const state = sliderAvailability(p.market, p.input, s.key);
              return (
                <SliderRow key={s.key} label={s.label} hint={state.hint ?? s.hint} value={p.input[s.key]} defaultValue={DEFAULT_INPUT[s.key]}
                           min={s.min} max={s.max} step={s.step} format={s.format} disabled={state.disabled}
                           onChange={(value) => p.dispatch({ type: "set", key: s.key, value })} />
              );
            })}
          </ControlSection>
        );
      })}
      <ControlSection title="Forecast" onReset={() => { p.onStart(p.defaultStart); p.onGrowth(0); }}
                      resetDisabled={p.start === p.defaultStart && p.growthPct === 0}>
        <div className="timeline__field">
          <span className="timeline__label">Changes start</span>
          <Select label="Week the changes start" value={p.start} onChange={p.onStart}
                  options={[{ value: p.defaultStart, label: `${formatMonth(p.defaultStart)} (right after the real data)` },
                            ...p.startOptions.map((w) => ({ value: w, label: formatMonth(w) }))]} />
        </div>
        <SliderRow label="Expected yearly growth" hint="Your assumption for future years. Without it the forecast stays flat." value={p.growthPct} defaultValue={0}
                   min={-5} max={10} step={0.5} format={(v) => `${formatSigned(v, String)}% a year`} onChange={p.onGrowth} />
      </ControlSection>
    </Card>
  );
}
