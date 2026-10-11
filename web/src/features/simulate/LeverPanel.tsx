import { marketName, SEASON_NAMES } from "../../content/labels";
import type { Dispatch } from "react";
import { Badge, Card, Chips, ControlSection, Select, SliderRow } from "../../components/ui";
import { formatMonth, formatPercent, formatSigned } from "../../data/format";
import type { ScheduleEffect } from "../../engine/planning";
import { activePreset, ALL_MARKETS, DEFAULT_INPUT, groupChanged, LEVER_GROUPS, PRESETS, presetAvailable, sliderAvailability,
         type LeverAction, type LeverInput } from "./levers";

interface LeverPanelProps {
  markets: Array<{ value: string; label: string }>;
  market: string; onMarket: (m: string) => void; coldStart: boolean;
  input: LeverInput; dispatch: Dispatch<LeverAction>;
  start: string; startOptions: string[]; onStart: (w: string) => void; defaultStart: string;
  growthPct: number; onGrowth: (pct: number) => void;
  season: string; schedule: ScheduleEffect | null;
  capacity: { years: number; central: number; range: [number, number]; seatChange: number };
}

const pct = (x: number) => formatPercent(x, 1);

/** What the schedule change does in the chosen season, in words. */
function ScheduleNote({ effect, season }: { effect: ScheduleEffect | null; season: string }) {
  if (!effect || effect.kind === "none") return null;
  if (effect.kind === "new_route") return <p className="note">New route: there is no past schedule to learn from, so the estimate uses similar markets.</p>;
  if (effect.kind === "closed") return <p className="note">Route closed: only visitors who arrive by other routes stay.</p>;
  return (
    <>
      <p className="note">
        {SEASON_NAMES[season] ?? season}: seats {pct(effect.seatChange)}, hotel nights {pct(effect.guestChange)} (range {pct(effect.range[0])} to {pct(effect.range[1])}).
      </p>
      {effect.kind === "pooled" && <p className="note">This market has no seat history of its own, so this uses the typical response across markets.</p>}
    </>
  );
}

const GROUP_NOTES: Record<string, string> = {
  schedule: "Learned from the past data: how this market's hotel guests followed its seats, day by day.",
  capacity: "The past data cannot show whether more seats brought more guests or more guests brought more seats.",
  assumptions: "Not learned from the data. Set them to test an idea.",
};

/** Left panel: which market, a starting point, the schedule change (learned), capacity growth and
 *  the other assumptions, and forecast settings. Which levers apply to which market is decided in
 *  levers.ts (sliderAvailability). */
export function LeverPanel(p: LeverPanelProps) {
  const all = p.market === ALL_MARKETS;
  return (
    <Card>
      <ControlSection title="Market">
        <Select label="Market" value={p.market} onChange={p.onMarket}
                options={[{ value: ALL_MARKETS, label: "All markets" }, ...p.markets.map((m) => ({ value: m.value, label: m.label.endsWith("(estimated from similar markets)") ? `${marketName(m.value)} (estimated from similar markets)` : marketName(m.value) }))]} />
        {all && <p className="note">Pick a market here or on the map to try flight changes.</p>}
        {p.coldStart && <Badge tone="neutral">No data of its own; estimated from similar markets</Badge>}
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
            {group.id === "capacity" && <Badge tone="neutral">Assumption</Badge>}
            <p className="note">{GROUP_NOTES[group.id]}</p>
            {p.market === "DOMESTIC" && group.id === "schedule" && <p className="note">UAE residents' stays do not depend on flights.</p>}
            {group.sliders.map((s) => {
              const state = sliderAvailability(p.market, p.input, s.key);
              return (
                <SliderRow key={s.key} label={s.label} hint={state.hint ?? s.hint} value={p.input[s.key]} defaultValue={DEFAULT_INPUT[s.key]}
                           min={s.min} max={s.max} step={s.step} format={s.format} disabled={state.disabled}
                           onChange={(value) => p.dispatch({ type: "set", key: s.key, value })} />
              );
            })}
            {group.id === "schedule" && <ScheduleNote effect={p.schedule} season={p.season} />}
            {group.id === "capacity" && p.input.capacityPct !== 0 && p.market !== "DOMESTIC" && !all && (
              <p className="note">
                After {p.capacity.years} years: seats {pct(p.capacity.seatChange)}, hotel nights {pct(p.capacity.central)} if guests keep pace with seats as they did in the past (a pattern, not a proven effect), anywhere from {pct(p.capacity.range[0])} to {pct(p.capacity.range[1])}.
              </p>
            )}
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
        <SliderRow label="Demand growth, all markets" hint="Your assumption for guest growth on top of any seat growth. Without it the forecast stays flat." value={p.growthPct} defaultValue={0}
                   min={-5} max={10} step={0.5} format={(v) => `${formatSigned(v, String)}% a year`} onChange={p.onGrowth} />
      </ControlSection>
    </Card>
  );
}
